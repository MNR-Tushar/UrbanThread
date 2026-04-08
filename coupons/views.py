from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .serializers import CouponSerializer, CouponValidationSerializer
from .models import Coupon
from rest_framework.response import Response
from datetime import date


class CouponViewset(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    def get_permissions(self):
        # FIX: authenticated users can list/retrieve/validate; only admins can create/update/delete
        if self.action in ['validate_coupon', 'list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def validate_coupon(self, request):
        serializer = CouponValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']

        try:
            coupon = Coupon.objects.get(code=code, is_active=True)

            if coupon.expiration_date < date.today():
                return Response(
                    {'error': 'Coupon has expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response({
                'valid': True,
                'discount': float(coupon.discount),
                'code': coupon.code,
                'message': f'Coupon applied! You get {coupon.discount}% off'
            })

        except Coupon.DoesNotExist:
            return Response(
                {'error': 'Invalid coupon code'},
                status=status.HTTP_404_NOT_FOUND
            )