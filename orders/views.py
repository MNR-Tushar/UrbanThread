from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema
from django.db import transaction
from decimal import Decimal
import uuid
import logging

from .serializers import OrderSerializer, OrderCreateSerializer
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from inventory.models import Inventory
from accounts.models import Address
from payments.models import Payment
from coupons.models import Coupon
from .tasks import (
    generate_sales_report,
    push_order_analytics_event,
    send_order_invoice_email,
    sync_order_stock,
)

logger = logging.getLogger(__name__)

@extend_schema_view(
    create_order=extend_schema(tags=['Orders']),
    cancel_order=extend_schema(tags=['Orders']),
    order_history=extend_schema(tags=['Orders']),
    export_sales_report=extend_schema(tags=['Orders']),
)
class OrderViewSet(viewsets.GenericViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(user=user).order_by('-created_at')

    @action(detail=False, methods=['post'])
    @extend_schema(
        request=OrderCreateSerializer,
        responses={201: OrderSerializer},
        description="Create an order from the authenticated user's cart."
    )
    def create_order(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        address_id = serializer.validated_data['address_id']
        payment_method = serializer.validated_data['payment_method']
        coupon_code = serializer.validated_data.get('coupon_code', '')

        user = request.user

        try:
            address = Address.objects.get(id=address_id, user=user)
        except Address.DoesNotExist:
            return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                try:
                    cart = Cart.objects.select_for_update().get(user=user)
                except Cart.DoesNotExist:
                    return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

                cart_items = CartItem.objects.select_for_update().filter(cart=cart).select_related(
                    'product', 'color', 'size'
                )

                if not cart_items.exists():
                    return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

                total_amount = Decimal('0.00')
                for item in cart_items:
                    price = item.product.discount_price if item.product.discount_price and item.product.discount_price > 0 else item.product.price
                    total_amount += Decimal(price) * item.quantity

                discount = Decimal('0.00')
                if coupon_code:
                    try:
                        coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                        from datetime import date
                        if coupon.expiration_date >= date.today():
                            discount = (total_amount * Decimal(coupon.discount)) / 100
                            total_amount -= discount
                    except Coupon.DoesNotExist:
                        pass

                order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"

                order = Order.objects.create(
                    order_number=order_number,
                    user=user,
                    total_amount=total_amount,
                    # FIX: use CharField values instead of booleans
                    payment_status='unpaid',
                    order_status='pending'
                )

                for item in cart_items:
                    price = item.product.discount_price if item.product.discount_price and item.product.discount_price > 0 else item.product.price

                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        color=item.color,
                        size=item.size,
                        quantity=item.quantity,
                        price=price
                    )

                    try:
                        inventory = Inventory.objects.select_for_update().get(
                            product=item.product,
                            color=item.color,
                            size=item.size
                        )
                    except Inventory.DoesNotExist:
                        raise Exception(f"Inventory not found for {item.product.product_name}")

                    if inventory.quantity < item.quantity:
                        raise Exception(f"Insufficient stock for {item.product.product_name}")

                    inventory.quantity -= item.quantity
                    inventory.save()

                Payment.objects.create(
                    user=user,
                    order=order,
                    payment_method=payment_method,
                    transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
                    amount=total_amount,
                    status='pending'
                )

                cart_items.delete()
                transaction.on_commit(lambda: send_order_invoice_email.delay(order.id))
                transaction.on_commit(lambda: sync_order_stock.delay(order.id))
                transaction.on_commit(lambda: push_order_analytics_event.delay(order.id, "order_placed"))

                return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def cancel_order(self, request, pk=None):
        try:
            order = Order.objects.get(id=pk, user=request.user)

            # FIX: check order_status string value, not boolean
            if order.order_status in ['completed', 'cancelled']:
                return Response(
                    {'error': f'Cannot cancel an order with status: {order.order_status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                for item in order.items.all():
                    try:
                        inventory = Inventory.objects.get(
                            product=item.product,
                            color=item.color,
                            size=item.size
                        )
                        inventory.quantity += item.quantity
                        inventory.save()
                    except Inventory.DoesNotExist:
                        return Response({'error': 'Inventory not found'}, status=status.HTTP_404_NOT_FOUND)

                # FIX: set to 'cancelled', not True
                order.order_status = 'cancelled'
                order.save()
                transaction.on_commit(lambda: push_order_analytics_event.delay(order.id, "order_cancelled"))

            return Response({'message': 'Order cancelled successfully'})

        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def order_history(self, request):
        orders = self.get_queryset()
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def export_sales_report(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Only admins can export reports'}, status=status.HTTP_403_FORBIDDEN)

        start_date = request.data.get('start_date', '')
        end_date = request.data.get('end_date', '')
        fmt = request.data.get('format', 'csv')
        if fmt not in ['csv', 'pdf']:
            return Response({'error': "format must be 'csv' or 'pdf'"}, status=status.HTTP_400_BAD_REQUEST)

        task = generate_sales_report.delay(start_date=start_date, end_date=end_date, fmt=fmt)
        return Response({'message': 'Report generation started', 'task_id': task.id}, status=status.HTTP_202_ACCEPTED)
