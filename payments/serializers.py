from rest_framework import serializers
from .models import Payment, PaymentLog
from orders.serializers import OrderSerializer


class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    is_successful = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'order', 'payment_method', 'payment_method_display',
            'transaction_id', 'status', 'status_display', 'amount', 'currency',
            'val_id', 'card_type', 'card_no', 'bank_tran_id', 'card_issuer',
            'card_brand', 'card_issuer_country', 'risk_level', 'risk_title',
            'error_message', 'is_successful', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'user', 'order', 'transaction_id', 'status', 'val_id', 'card_type',
            'card_no', 'bank_tran_id', 'card_issuer', 'card_brand',
            'card_issuer_country', 'risk_level', 'risk_title', 'created_at',
            'updated_at', 'completed_at'
        ]


class PaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLog
        fields = '__all__'
        read_only_fields = ['created_at']


class InitiatePaymentSerializer(serializers.Serializer):
    """Serializer for initiating SSL Commerce payment"""
    order_number = serializers.CharField(required=True)
    payment_method = serializers.ChoiceField(
        choices=['sslcommerz', 'cash_on_delivery'],
        default='sslcommerz'
    )
    
    def validate_order_number(self, value):
        from orders.models import Order
        try:
            order = Order.objects.get(order_number=value, user=self.context['request'].user)
            if hasattr(order, 'payment'):
                if order.payment.status == 'completed':
                    raise serializers.ValidationError("This order has already been paid")
            return order.id  # Return order ID for later use
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found")


class PaymentCallbackSerializer(serializers.Serializer):
    """Serializer for SSL Commerce callback data"""
    status = serializers.CharField()
    tran_id = serializers.CharField()
    val_id = serializers.CharField(required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    card_type = serializers.CharField(required=False)
    store_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    bank_tran_id = serializers.CharField(required=False)
    card_issuer = serializers.CharField(required=False)
    card_brand = serializers.CharField(required=False)
    card_no = serializers.CharField(required=False)
    card_issuer_country = serializers.CharField(required=False)
    currency = serializers.CharField(required=False)
    risk_level = serializers.CharField(required=False)
    risk_title = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
    
    # Optional fields from response
    value_a = serializers.CharField(required=False)  # order_id
    value_b = serializers.CharField(required=False)
    value_c = serializers.CharField(required=False)
    value_d = serializers.CharField(required=False)


class RefundPaymentSerializer(serializers.Serializer):
    """Serializer for refund requests"""
    payment_id = serializers.IntegerField(required=True)
    refund_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    refund_reason = serializers.CharField(required=True, max_length=500)
    
    def validate_payment_id(self, value):
        try:
            payment = Payment.objects.get(id=value)
            if payment.status != 'completed':
                raise serializers.ValidationError("Can only refund completed payments")
            if not payment.bank_tran_id:
                raise serializers.ValidationError("No bank transaction ID found for refund")
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found")
    
    def validate(self, data):
        payment = Payment.objects.get(id=data['payment_id'])
        if data['refund_amount'] > payment.amount:
            raise serializers.ValidationError({
                'refund_amount': 'Refund amount cannot exceed payment amount'
            })
        return data