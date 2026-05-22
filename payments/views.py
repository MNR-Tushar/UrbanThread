from django.shortcuts import redirect
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

import uuid
import logging

from .models import Payment, PaymentLog
from .serializers import (
    PaymentSerializer, PaymentLogSerializer, InitiatePaymentSerializer,
    PaymentCallbackSerializer, RefundPaymentSerializer
)
from .utils import SSLCommerzPayment
from .tasks import retry_payment_verification
from orders.models import Order
from orders.tasks import push_order_analytics_event
from accounts.models import Address

logger = logging.getLogger(__name__)


@extend_schema(tags=["Payments - History"])
class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing payment history
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all().select_related('user', 'order')
        return Payment.objects.filter(user=user).select_related('order')
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get payment logs for a specific payment"""
        payment = self.get_object()
        logs = PaymentLog.objects.filter(payment=payment)
        serializer = PaymentLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_payments(self, request):
        """Get current user's payment history"""
        payments = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)


@extend_schema(tags=["Payments - Initiate"])
class InitiatePaymentView(APIView):
    """
    Initiate SSL Commerce Payment
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=InitiatePaymentSerializer,
        responses={200: dict, 400: dict, 404: dict},
        description="Initiate payment for an existing order using SSLCommerz or Cash on Delivery."
    )
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data['order_number']  
        payment_method = serializer.validated_data['payment_method']
        
        try:
            order = Order.objects.select_related('user').get(
                id=order_id,
                user=request.user
            )
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if order already has a completed payment
        if hasattr(order, 'payment') and order.payment.status == 'completed':
            return Response(
                {'error': 'Order already paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle Cash on Delivery
        if payment_method == 'cash_on_delivery':
            transaction_id = f"COD-{uuid.uuid4().hex[:12].upper()}"
            
            # Create or update payment
            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'user': request.user,
                    'payment_method': 'cash_on_delivery',
                    'transaction_id': transaction_id,
                    'status': 'pending',
                    'amount': order.total_amount,
                    'currency': 'BDT'
                }
            )
            
            if not created:
                payment.transaction_id = transaction_id
                payment.status = 'pending'
                payment.save()
            
            return Response({
                'success': True,
                'payment_method': 'cash_on_delivery',
                'order_id': order.id,
                'order_number': order.order_number,
                'amount': str(order.total_amount),
                'transaction_id': transaction_id
            })
        
        # Handle SSL Commerce Payment
        if payment_method == 'sslcommerz':
            # Create unique transaction ID
            transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            
            # Create or update payment record
            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'user': request.user,
                    'payment_method': 'sslcommerz',
                    'transaction_id': transaction_id,
                    'status': 'pending',
                    'amount': order.total_amount,
                    'currency': 'BDT'
                }
            )
            
            if not created:
                payment.transaction_id = transaction_id
                payment.status = 'pending'
                payment.save()
            
            # Prepare payment data for SSL Commerce
            base_url = request.build_absolute_uri('/')[:-1]
            
            payment_data = {
                'total_amount': float(order.total_amount),
                'currency': 'BDT',
                'tran_id': transaction_id,
                'success_url': f"{base_url}/payments/sslcommerz/success/",
                'fail_url': f"{base_url}/payments/sslcommerz/fail/",
                'cancel_url': f"{base_url}/payments/sslcommerz/cancel/",
                'ipn_url': f"{base_url}/payments/sslcommerz/ipn/",
                
                # Customer info
                'cus_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                'cus_email': request.user.email,
                'cus_phone': request.user.phone or '01700000000',
                'cus_add1': request.user.address or 'Dhaka, Bangladesh',
                'cus_city': 'Dhaka',
                'cus_country': 'Bangladesh',
                
                # Product info
                'product_name': f"Order #{order.order_number}",
                'product_category': 'ecommerce',
                'product_profile': 'general',
                
                # Optional - store order ID
                'value_a': str(order.id),
            }
            
            # Initialize SSL Commerce
            sslcz = SSLCommerzPayment()
            response = sslcz.create_session(payment_data)
            
            # Log the initiation
            log_data = response.copy() if isinstance(response, dict) else {}
            # Convert Decimal values to strings for JSON serialization
            if 'total_amount' in log_data:
                log_data['total_amount'] = str(log_data['total_amount'])
            if 'amount' in log_data:
                log_data['amount'] = str(log_data['amount'])
                
            PaymentLog.objects.create(
                payment=payment,
                event_type='payment_initiated',
                event_data=log_data,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            if response.get('status') == 'SUCCESS':
                payment.status = 'processing'
                payment.response_data = response
                payment.save()
                
                return Response({
                    'success': True,
                    'gateway_url': response.get('GatewayPageURL'),
                    'session_key': response.get('sessionkey'),
                    'transaction_id': transaction_id
                })
            else:
                payment.status = 'failed'
                payment.error_message = response.get('message', 'Payment initiation failed')
                payment.save()
                
                return Response({
                    'success': False,
                    'error': response.get('message', 'Payment initiation failed')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {'error': 'Invalid payment method'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@extend_schema(tags=["Payments - Callbacks"])
class SSLCommerzSuccessView(APIView):
    """Handle SSL Commerce success callback"""
    permission_classes = [AllowAny]
    
    @csrf_exempt
    def post(self, request):
        serializer = PaymentCallbackSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"Invalid callback data: {serializer.errors}")
            return redirect(f"{settings.FRONTEND_URL}/payment/failed")
        
        tran_id = serializer.validated_data.get('tran_id')
        val_id = serializer.validated_data.get('val_id')
        callback_status = serializer.validated_data.get('status')
        
        try:
            payment = Payment.objects.select_related('order').get(transaction_id=tran_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for transaction: {tran_id}")
            return redirect(f"{settings.FRONTEND_URL}/payment/failed")
        
        # Log the callback
        callback_log_data = serializer.validated_data.copy() if isinstance(serializer.validated_data, dict) else {}
        # Convert Decimal values to strings for JSON serialization
        if 'total_amount' in callback_log_data:
            callback_log_data['total_amount'] = str(callback_log_data['total_amount'])
        if 'amount' in callback_log_data:
            callback_log_data['amount'] = str(callback_log_data['amount'])
        if 'currency_amount' in callback_log_data:
            callback_log_data['currency_amount'] = str(callback_log_data['currency_amount'])
            
        PaymentLog.objects.create(
            payment=payment,
            event_type='success_callback',
            event_data=callback_log_data,
            ip_address=self.get_client_ip(request)
        )
        
        # Validate with SSL Commerce
        if val_id and callback_status in ['VALID', 'VALIDATED']:
            sslcz = SSLCommerzPayment()
            validation_response = sslcz.validate_payment(val_id, tran_id)
            
            # Log validation
            validation_log_data = validation_response.copy() if isinstance(validation_response, dict) else {}
            # Convert Decimal values to strings for JSON serialization
            if 'total_amount' in validation_log_data:
                validation_log_data['total_amount'] = str(validation_log_data['total_amount'])
            if 'amount' in validation_log_data:
                validation_log_data['amount'] = str(validation_log_data['amount'])
                
            PaymentLog.objects.create(
                payment=payment,
                event_type='validation_response',
                event_data=validation_log_data
            )
            
            if validation_response.get('status') == 'VALID' or validation_response.get('status') == 'VALIDATED':
                with transaction.atomic():
                    # Update payment
                    payment.status = 'completed'
                    payment.val_id = val_id
                    payment.card_type = serializer.validated_data.get('card_type', '')
                    payment.card_no = serializer.validated_data.get('card_no', '')
                    payment.bank_tran_id = serializer.validated_data.get('bank_tran_id', '')
                    payment.card_issuer = serializer.validated_data.get('card_issuer', '')
                    payment.card_brand = serializer.validated_data.get('card_brand', '')
                    payment.card_issuer_country = serializer.validated_data.get('card_issuer_country', '')
                    payment.risk_level = serializer.validated_data.get('risk_level', '')
                    payment.risk_title = serializer.validated_data.get('risk_title', '')
                    payment.completed_at = timezone.now()
                    payment.response_data = validation_response
                    payment.save()
                    
                    # Update order
                    payment.order.payment_status = 'paid'
                    payment.order.order_status = 'processing'
                    payment.order.save()
                    transaction.on_commit(lambda: push_order_analytics_event.delay(payment.order.id, "payment_completed"))
                
                return redirect(
                    f"{settings.FRONTEND_URL}/payment/success?order_id={payment.order.id}&transaction_id={tran_id}"
                )
        
        # If validation failed
        payment.status = 'failed'
        payment.error_message = 'Payment validation failed'
        payment.save()
        retry_payment_verification.delay(payment.id)
        
        return redirect(f"{settings.FRONTEND_URL}/payment/failed?transaction_id={tran_id}")
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@extend_schema(tags=["Payments - Callbacks"])
class SSLCommerzFailView(APIView):
    """Handle SSL Commerce fail callback"""
    permission_classes = [AllowAny]
    
    @csrf_exempt
    def post(self, request):
        tran_id = request.data.get('tran_id')
        
        try:
            payment = Payment.objects.get(transaction_id=tran_id)
            payment.status = 'failed'
            payment.error_message = request.data.get('error', 'Payment failed')
            payment.response_data = request.data
            payment.save()
            
            # Log the failure
            fail_log_data = request.data.copy() if isinstance(request.data, dict) else {}
            # Convert Decimal values to strings for JSON serialization
            if 'total_amount' in fail_log_data:
                fail_log_data['total_amount'] = str(fail_log_data['total_amount'])
            if 'amount' in fail_log_data:
                fail_log_data['amount'] = str(fail_log_data['amount'])
            if 'currency_amount' in fail_log_data:
                fail_log_data['currency_amount'] = str(fail_log_data['currency_amount'])
                
            PaymentLog.objects.create(
                payment=payment,
                event_type='fail_callback',
                event_data=fail_log_data
            )
            retry_payment_verification.delay(payment.id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for failed transaction: {tran_id}")
        
        return redirect(f"{settings.FRONTEND_URL}/payment/failed?transaction_id={tran_id}")


@extend_schema(tags=["Payments - Callbacks"])
class SSLCommerzCancelView(APIView):
    """Handle SSL Commerce cancel callback"""
    permission_classes = [AllowAny]
    
    @csrf_exempt
    def post(self, request):
        tran_id = request.data.get('tran_id')
        
        try:
            payment = Payment.objects.get(transaction_id=tran_id)
            payment.status = 'cancelled'
            payment.response_data = request.data
            payment.save()
            
            # Log the cancellation
            cancel_log_data = request.data.copy() if isinstance(request.data, dict) else {}
            # Convert Decimal values to strings for JSON serialization
            if 'total_amount' in cancel_log_data:
                cancel_log_data['total_amount'] = str(cancel_log_data['total_amount'])
            if 'amount' in cancel_log_data:
                cancel_log_data['amount'] = str(cancel_log_data['amount'])
            if 'currency_amount' in cancel_log_data:
                cancel_log_data['currency_amount'] = str(cancel_log_data['currency_amount'])
                
            PaymentLog.objects.create(
                payment=payment,
                event_type='cancel_callback',
                event_data=cancel_log_data
            )
            retry_payment_verification.delay(payment.id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for cancelled transaction: {tran_id}")
        
        return redirect(f"{settings.FRONTEND_URL}/payment/cancelled?transaction_id={tran_id}")


@extend_schema(tags=["Payments - IPN"])
class SSLCommerzIPNView(APIView):
    """Handle SSL Commerce IPN (Instant Payment Notification)"""
    permission_classes = [AllowAny]
    
    @csrf_exempt
    def post(self, request):
        """
        IPN is called by SSL Commerce server to notify about payment status
        This is the most reliable way to update payment status
        """
        tran_id = request.data.get('tran_id')
        val_id = request.data.get('val_id')
        
        try:
            payment = Payment.objects.select_related('order').get(transaction_id=tran_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for IPN: {tran_id}")
            return HttpResponse('FAILED')
        
        # Log IPN
        ipn_log_data = request.data.copy() if isinstance(request.data, dict) else {}
        # Convert Decimal values to strings for JSON serialization
        if 'total_amount' in ipn_log_data:
            ipn_log_data['total_amount'] = str(ipn_log_data['total_amount'])
        if 'amount' in ipn_log_data:
            ipn_log_data['amount'] = str(ipn_log_data['amount'])
        if 'currency_amount' in ipn_log_data:
            ipn_log_data['currency_amount'] = str(ipn_log_data['currency_amount'])
            
        PaymentLog.objects.create(
            payment=payment,
            event_type='ipn_received',
            event_data=ipn_log_data
        )
        
        # Validate the payment
        if val_id:
            sslcz = SSLCommerzPayment()
            validation_response = sslcz.validate_payment(val_id, tran_id)
            
            ipn_validation_log_data = validation_response.copy() if isinstance(validation_response, dict) else {}
            # Convert Decimal values to strings for JSON serialization
            if 'total_amount' in ipn_validation_log_data:
                ipn_validation_log_data['total_amount'] = str(ipn_validation_log_data['total_amount'])
            if 'amount' in ipn_validation_log_data:
                ipn_validation_log_data['amount'] = str(ipn_validation_log_data['amount'])
                
            PaymentLog.objects.create(
                payment=payment,
                event_type='ipn_validation',
                event_data=ipn_validation_log_data
            )
            
            if validation_response.get('status') in ['VALID', 'VALIDATED']:
                if payment.status != 'completed':
                    with transaction.atomic():
                        payment.mark_as_completed()
                        payment.val_id = val_id
                        payment.save()
                        transaction.on_commit(lambda: push_order_analytics_event.delay(payment.order.id, "payment_completed"))
                
                return HttpResponse('SUCCESS')
            retry_payment_verification.delay(payment.id)
        
        return HttpResponse('FAILED')


@extend_schema(tags=["Payments - Refunds"])
class RefundPaymentView(APIView):
    """
    Initiate payment refund (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        serializer = RefundPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment_id = serializer.validated_data['payment_id']
        refund_amount = serializer.validated_data['refund_amount']
        refund_reason = serializer.validated_data['refund_reason']
        
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Initiate refund with SSL Commerce
        sslcz = SSLCommerzPayment()
        refund_response = sslcz.refund_payment(
            bank_tran_id=payment.bank_tran_id,
            refund_amount=refund_amount,
            refund_remarks=refund_reason
        )
        
        # Log refund attempt
        PaymentLog.objects.create(
            payment=payment,
            event_type='refund_initiated',
            event_data={
                'refund_amount': str(refund_amount),
                'refund_reason': refund_reason,
                'response': refund_response
            }
        )
        
        if refund_response.get('status') == 'success':
            payment.status = 'refunded'
            payment.save()
            
            # Update order
            payment.order.payment_status = 'refunded'
            payment.order.save()
            
            return Response({
                'success': True,
                'message': 'Refund initiated successfully',
                'refund_ref_id': refund_response.get('refund_ref_id')
            })
        
        return Response({
            'success': False,
            'error': refund_response.get('message', 'Refund failed')
        }, status=status.HTTP_400_BAD_REQUEST)
