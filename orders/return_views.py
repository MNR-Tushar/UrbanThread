from rest_framework import serializers, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.exceptions import ValidationError, PermissionDenied

from .models import Order, ReturnRequest


class ReturnRequestSerializer(serializers.ModelSerializer):
    order_id = serializers.PrimaryKeyRelatedField(source='order', queryset=Order.objects.all(), write_only=True, required=True)
    order = serializers.IntegerField(source='order_id', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = ReturnRequest
        fields = ['id', 'order', 'order_id', 'order_number', 'reason', 'status', 'admin_note', 'created_at', 'updated_at']
        read_only_fields = ['status', 'admin_note', 'created_at', 'updated_at']

    def validate(self, attrs):
        request = self.context['request']
        order = attrs['order']
        if order.order_status not in ['delivered', 'completed']:
            raise ValidationError({'order_id': 'A return can be requested after delivery.'})
        if request.user.is_authenticated:
            if order.user_id != request.user.id:
                raise PermissionDenied('This order does not belong to you.')
        elif not request.headers.get('X-Guest-Cart') or order.guest_token != request.headers.get('X-Guest-Cart'):
            raise PermissionDenied('This order does not belong to this guest checkout.')
        if order.return_requests.filter(status__in=['pending', 'approved', 'completed']).exists():
            raise ValidationError({'order_id': 'A return request is already active for this order.'})
        return attrs


class AdminReturnRequestSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    class Meta:
        model = ReturnRequest
        fields = ['id', 'order_number', 'reason', 'status', 'admin_note', 'created_at', 'updated_at']


class ReturnRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.user.is_staff and self.action in ['update', 'partial_update']:
            return AdminReturnRequestSerializer
        return ReturnRequestSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    def get_queryset(self):
        if self.request.user.is_staff:
            return ReturnRequest.objects.select_related('order', 'user').all()
        if self.request.user.is_authenticated:
            return ReturnRequest.objects.filter(user=self.request.user).select_related('order')
        token = self.request.headers.get('X-Guest-Cart', '')
        return ReturnRequest.objects.filter(order__guest_token=token).select_related('order') if token else ReturnRequest.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)
