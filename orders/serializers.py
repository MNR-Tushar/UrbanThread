from rest_framework import serializers
from .models import *
from products.serializers import *
from accounts.serializers import CustomUserSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product=ProductListSerializer(read_only=True)
    color=ColorSerializer(read_only=True)
    size=SizeSerializer(read_only=True)
    subtotal=serializers.SerializerMethodField()

   
    
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'color', 'size', 'quantity', 'price', 'subtotal', 'created_at', 'updated_at']
        read_only_fields = ['order', 'created_at', 'updated_at']
    
    
    def get_subtotal(self, obj):
        return float(obj.price * obj.quantity)
    
class OrderSerializer(serializers.ModelSerializer):
    user=CustomUserSerializer(read_only=True)
    items=OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number','user','total_amount', 'payment_status', 'order_status', 'items','created_at', 'updated_at']
        read_only_fields = ['order_number', 'user', 'created_at', 'updated_at']
        
        

class OrderCreateSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.CharField(required=True)
    
    def validate_payment_method(self, value):
        allowed_methods = ['cash_on_delivery', 'stripe', 'paypal']
        if value not in allowed_methods:
            raise serializers.ValidationError(
                f"Payment method must be one of: {', '.join(allowed_methods)}"
            )
        return value