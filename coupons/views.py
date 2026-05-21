from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.core.cache import cache
from datetime import date

from .serializers import CouponSerializer, CouponValidationSerializer
from .models import Coupon


# ─── Cache Key Helpers ────────────────────────────────────────────────────────

def _coupon_list_key() -> str:
    return "coupon_list"

def _coupon_detail_key(pk) -> str:
    return f"coupon_detail:{pk}"

def _coupon_validate_key(code: str) -> str:
    return f"coupon_valid:{code}"


COUPON_CACHE_TTL    = 60 * 30   # 30 minutes
VALIDATE_CACHE_TTL  = 60 * 5    # 5 minutes 


class CouponViewset(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    def get_permissions(self):
        if self.action in ['validate_coupon', 'list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    # ─── List ─────────────────────────────────────────────────────────────────

    def list(self, request, *args, **kwargs):
        cache_key = _coupon_list_key()
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=COUPON_CACHE_TTL)
        return response

    # ─── Retrieve ─────────────────────────────────────────────────────────────

    def retrieve(self, request, *args, **kwargs):
        cache_key = _coupon_detail_key(kwargs.get('pk'))
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=COUPON_CACHE_TTL)
        return response

    # ─── Cache Invalidation ───────────────────────────────────────────────────

    def _invalidate_coupon_cache(self, pk=None, code=None):
        cache.delete(_coupon_list_key())
        if pk:
            cache.delete(_coupon_detail_key(pk))
        if code:
            cache.delete(_coupon_validate_key(code))

    def perform_create(self, serializer):
        instance = serializer.save()
        self._invalidate_coupon_cache()

    def perform_update(self, serializer):
        instance = serializer.save()
        self._invalidate_coupon_cache(pk=instance.pk, code=instance.code)

    def perform_destroy(self, instance):
        self._invalidate_coupon_cache(pk=instance.pk, code=instance.code)
        instance.delete()

    # ─── Validate Coupon ──────────────────────────────────────────────────────

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def validate_coupon(self, request):
        serializer = CouponValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']

        # Cache hit check
        cache_key = _coupon_validate_key(code)
        cached = cache.get(cache_key)
        if cached is not None:
            # Cached 'invalid' response check
            if not cached.get('valid'):
                return Response({'error': cached.get('error')}, status=status.HTTP_400_BAD_REQUEST)
            return Response(cached)

        try:
            coupon = Coupon.objects.get(code=code, is_active=True)

            if coupon.start_date and coupon.start_date > date.today():
                data = {'valid': False, 'error': 'Coupon campaign has not started yet'}
                cache.set(cache_key, data, timeout=VALIDATE_CACHE_TTL)
                return Response({'error': 'Coupon campaign has not started yet'}, status=status.HTTP_400_BAD_REQUEST)

            if coupon.expiration_date < date.today():
                data = {'valid': False, 'error': 'Coupon has expired'}
                cache.set(cache_key, data, timeout=VALIDATE_CACHE_TTL)
                return Response({'error': 'Coupon has expired'}, status=status.HTTP_400_BAD_REQUEST)

            data = {
                'valid':    True,
                'discount': float(coupon.discount),
                'code':     coupon.code,
                'message':  f'Coupon applied! You get {coupon.discount}% off',
            }
            cache.set(cache_key, data, timeout=VALIDATE_CACHE_TTL)
            return Response(data)

        except Coupon.DoesNotExist:
            data = {'valid': False, 'error': 'Invalid coupon code'}
            cache.set(cache_key, data, timeout=VALIDATE_CACHE_TTL)
            return Response({'error': 'Invalid coupon code'}, status=status.HTTP_404_NOT_FOUND)
