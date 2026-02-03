
from rest_framework import viewsets,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from django.db import transaction
from decimal import Decimal
import uuid

from .serializers import *
from .models import *
from cart.models import *
from inventory.models import *
from products.models import *
from accounts.models import *
from payments.models import *
from coupons.models import *



class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(user=user).order_by('-created_at')
    
    
    @action(detail=False, methods=['post'])
    def create_order(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        address_id = serializer.validated_data['address_id']
        payment_method = serializer.validated_data['payment_method']
        coupon_code = serializer.validated_data['coupon_code']
        
        user = request.user
        
        try:
            address=Address.objects.get(id=address_id,user=user)
        except Address.DoesNotExist:
            return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
        
        total_amount = Decimal('0.00')
        for item in CartItem:
            price = item.product.discount_price if item.product.discount_price > 0 else item.product.price
            total_amount += price * item.quantity
        
        # Apply coupon if provided
        discount = Decimal('0.00')
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                from datetime import date
                if coupon.expiration_date >= date.today():
                    discount = (total_amount * coupon.discount) / 100
                    total_amount -= discount
            except Coupon.DoesNotExist:
                pass
        
        # Create order with transaction
        try:
            with transaction.atomic():
                # Generate order number
                order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
                
                # Create order
                order = Order.objects.create(
                    order_number=order_number,
                    user=request.user,
                    total_amount=total_amount,
                    payment_status=False,
                    order_status=False
                )
                
                # Create order items and update inventory
                for item in CartItem:
                    price = item.product.discount_price if item.product.discount_price > 0 else item.product.price
                    
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        color=item.color,
                        size=item.size,
                        quantity=item.quantity,
                        price=price
                    )
                    
                    # Update inventory
                    inventory = Inventory.objects.get(
                        product=item.product,
                        color=item.color,
                        size=item.size
                    )
                    
                    if inventory.quantity < item.quantity:
                        raise Exception(f"Insufficient stock for {item.product.name}")
                    
                    inventory.quantity -= item.quantity
                    inventory.save()
                
                # Create payment record
                payment_status = True if payment_method == 'cash_on_delivery' else False
                Payment.objects.create(
                    user=request.user,
                    order=order,
                    payment_method=payment_method,
                    tranction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
                    status=payment_status
                )
                
                # Clear cart
                CartItem.delete()
                
                # Return order
                order_serializer = OrderSerializer(order)
                return Response(order_serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['patch'])
    def cancel_order(self, request, pk=None):
        try:
            order = Order.objects.get(id=pk, user=request.user)
            
            if order.order_status:
                return Response(
                    {'error': 'Cannot cancel completed order'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Restore inventory
            with transaction.atomic():
                for item in order.orderitem_set.all():
                    inventory = Inventory.objects.get(
                        product=item.product,
                        color=item.color,
                        size=item.size
                    )
                    inventory.quantity += item.quantity
                    inventory.save()
                
                order.order_status = True  # Mark as cancelled/completed
                order.save()
            
            return Response({'message': 'Order cancelled successfully'})
            
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def order_history(self, request):
        orders = self.get_queryset()
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)