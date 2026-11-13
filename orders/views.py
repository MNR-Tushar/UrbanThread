from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema
from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from decimal import Decimal
import uuid
import logging

from .serializers import OrderSerializer, OrderCreateSerializer
from .models import Order, OrderItem, OrderStatusHistory
from cart.models import Cart, CartItem
from inventory.models import Inventory
from accounts.models import Address
from payments.models import Payment
from coupons.models import Coupon
from products.models import StoreSettings
from .tasks import (
    generate_sales_report,
    push_order_analytics_event,
    send_order_invoice_email,
    sync_order_stock,
)

logger = logging.getLogger(__name__)


def _enqueue_task(task, *args):
    """Keep a completed order successful when the optional Celery broker is offline."""
    try:
        task.delay(*args)
    except Exception:
        logger.exception("Could not queue background task %s", task.name)

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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def admin_dashboard(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({'detail': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        from accounts.models import CustomUser
        from inventory.models import Inventory
        from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
        today = timezone.localdate()
        period = request.query_params.get('period', 'daily')
        truncator, span = {'weekly': (TruncWeek, 84), 'monthly': (TruncMonth, 365)}.get(period, (TruncDate, 6))
        recent_days = today - timedelta(days=span)
        orders = Order.objects.select_related('user').prefetch_related('items__product').order_by('-created_at')
        daily = (Order.objects.filter(created_at__date__gte=recent_days, created_at__date__lte=today)
                 .exclude(order_status='cancelled').annotate(day=truncator('created_at'))
                 .values('day').annotate(sales=Sum('total_amount'), orders=Count('id')).order_by('day'))
        return Response({
            'today_sales': Order.objects.filter(created_at__date=today).exclude(order_status='cancelled').aggregate(total=Sum('total_amount'))['total'] or 0,
            'total_orders': Order.objects.count(),
            'pending_orders': Order.objects.filter(order_status='pending').count(),
            'customers': CustomUser.objects.filter(is_staff=False, is_superuser=False).count(),
            'daily_sales': list(daily),
            'low_stock': list(Inventory.objects.filter(quantity__lte=5).select_related('product', 'color', 'size').values('id', 'quantity', 'product__product_name', 'color__color', 'size__size_type')[:12]),
            'recent_orders': OrderSerializer(orders[:8], many=True).data,
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def admin_orders(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({'detail': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        orders = Order.objects.select_related('user').prefetch_related('items__product').order_by('-created_at')
        selected_status = request.query_params.get('status')
        if selected_status:
            orders = orders.filter(order_status=selected_status)
        return Response(OrderSerializer(orders, many=True).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def admin_update_status(self, request, pk=None):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({'detail': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        order = Order.objects.filter(pk=pk).first()
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        next_status = request.data.get('order_status')
        allowed = {key for key, _ in Order.ORDER_STATUS_CHOICES}
        if next_status not in allowed:
            return Response({'order_status': ['Choose a valid order status.']}, status=status.HTTP_400_BAD_REQUEST)
        previous_status = order.order_status
        order.order_status = next_status
        order.save(update_fields=['order_status', 'updated_at'])
        if previous_status != next_status:
            OrderStatusHistory.objects.create(order=order, status=next_status, note=f'Status changed from {previous_status} to {next_status}.')
        return Response(OrderSerializer(order).data)

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(user=user).order_by('-created_at')

    def retrieve(self, request, pk=None):
        order = self.get_queryset().filter(pk=pk).first()
        if order is None:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)

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

                settings_row = StoreSettings.objects.order_by('id').first()
                city = (address.city or '').strip().lower()
                shipping_fee = (settings_row.dhaka_delivery_fee if settings_row else Decimal('70.00')) if city in ('dhaka', 'ঢাকা') else (settings_row.outside_delivery_fee if settings_row else Decimal('130.00'))
                total_amount += Decimal(shipping_fee)

                order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"

                order = Order.objects.create(
                    order_number=order_number,
                    user=user,
                    total_amount=total_amount,
                    shipping_fee=shipping_fee,
                    # FIX: use CharField values instead of booleans
                    payment_status='unpaid',
                    order_status='pending',
                    shipping_address={
                        'full_name': address.full_name, 'phone': address.phone,
                        'city': address.city, 'state': address.state,
                        'pincode': address.pincode, 'address': address.address,
                    },
                )
                OrderStatusHistory.objects.create(order=order, status='pending', note='Order placed.')

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
                    cache.delete(f"inventory_avail:{item.product_id}:{item.color_id}:{item.size_id}")
                    cache.delete(f"product_inventory:{item.product_id}")

                Payment.objects.create(
                    user=user,
                    order=order,
                    payment_method=payment_method,
                    transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
                    amount=total_amount,
                    status='pending'
                )

                cart_items.delete()
                transaction.on_commit(lambda: cache.delete(f"cart:{user.id}"))
                transaction.on_commit(lambda: _enqueue_task(send_order_invoice_email, order.id))
                transaction.on_commit(lambda: _enqueue_task(sync_order_stock, order.id))
                transaction.on_commit(lambda: _enqueue_task(push_order_analytics_event, order.id, "order_placed"))

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
                        cache.delete(f"inventory_avail:{item.product_id}:{item.color_id}:{item.size_id}")
                        cache.delete(f"product_inventory:{item.product_id}")
                    except Inventory.DoesNotExist:
                        return Response({'error': 'Inventory not found'}, status=status.HTTP_404_NOT_FOUND)

                # FIX: set to 'cancelled', not True
                order.order_status = 'cancelled'
                order.save()
                OrderStatusHistory.objects.create(order=order, status='cancelled', note='Order cancelled by customer.')
                transaction.on_commit(lambda: _enqueue_task(push_order_analytics_event, order.id, "order_cancelled"))

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
