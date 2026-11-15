from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from products.serializers import ProductListSerializer, ColorSerializer, SizeSerializer
from accounts.serializers import CustomUserSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    color = ColorSerializer(read_only=True)
    size = SizeSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'color', 'size', 'quantity', 'price', 'subtotal', 'created_at', 'updated_at']
        read_only_fields = ['order', 'created_at', 'updated_at']

    def get_subtotal(self, obj):
        return float(obj.price * obj.quantity)


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'status_display', 'note', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True, allow_null=True)
    # FIX: related_name on OrderItem FK is now 'items' (set in orders/models.py)
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'user', 'total_amount', 'shipping_fee', 'payment_status',
                  'order_status', 'shipping_address', 'customer_name', 'customer_email', 'courier_name', 'courier_tracking_id', 'courier_tracking_url', 'status_history', 'items', 'created_at', 'updated_at']
        read_only_fields = ['order_number', 'user', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=False)
    guest_name = serializers.CharField(required=False, max_length=120)
    guest_email = serializers.EmailField(required=False)
    guest_phone = serializers.CharField(required=False, max_length=20)
    city = serializers.CharField(required=False, max_length=100)
    state = serializers.CharField(required=False, max_length=100)
    pincode = serializers.CharField(required=False, max_length=10)
    address = serializers.CharField(required=False, max_length=500)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    # FIX: payment_method is required and does not allow blank
    payment_method = serializers.CharField(required=True)

    def validate(self, attrs):
        request = self.context['request']
        if request.user.is_authenticated:
            if not attrs.get('address_id'):
                raise serializers.ValidationError({'address_id': 'Select a saved delivery address.'})
        else:
            required = ['guest_name', 'guest_email', 'guest_phone', 'city', 'state', 'pincode', 'address']
            missing = [field for field in required if not attrs.get(field)]
            if missing:
                raise serializers.ValidationError({field: 'This field is required for guest checkout.' for field in missing})
            if attrs.get('payment_method') != 'cash_on_delivery':
                raise serializers.ValidationError({'payment_method': 'Guest checkout currently supports cash on delivery.'})
        return attrs

    def validate_payment_method(self, value):
        allowed_methods = ['cash_on_delivery', 'sslcommerz']
        if value not in allowed_methods:
            raise serializers.ValidationError(
                f"Payment method must be one of: {', '.join(allowed_methods)}"
            )
        return value
