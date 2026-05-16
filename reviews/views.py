from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.cache import cache

from .models import Review
from .serializers import ReviewSerializer


# ─── Cache Key Helpers ────────────────────────────────────────────────────────

def _review_list_key(product_id=None) -> str:
    if product_id:
        return f"review_list:product:{product_id}"
    return "review_list:all"

def _review_detail_key(pk) -> str:
    return f"review_detail:{pk}"


REVIEW_CACHE_TTL = 60 * 10  # 10 minutes


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Review.objects.select_related('user', 'product').all()
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset

    # ─── List ─────────────────────────────────────────────────────────────────

    def list(self, request, *args, **kwargs):
        product_id = request.query_params.get('product_id')
        cache_key = _review_list_key(product_id)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response_from_cache(cached)

        from rest_framework.response import Response
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=REVIEW_CACHE_TTL)
        return response

    # ─── Retrieve ─────────────────────────────────────────────────────────────

    def retrieve(self, request, *args, **kwargs):
        from rest_framework.response import Response
        cache_key = _review_detail_key(kwargs.get('pk'))
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=REVIEW_CACHE_TTL)
        return response

    # ─── Cache Invalidation ───────────────────────────────────────────────────

    def _invalidate_review_cache(self, product_id=None, pk=None):
        # Invalidate all review caches
        cache.delete(_review_list_key())
        if product_id:
            cache.delete(_review_list_key(product_id))
        if pk:
            cache.delete(_review_detail_key(pk))

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        self._invalidate_review_cache(product_id=instance.product_id)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._invalidate_review_cache(product_id=instance.product_id, pk=instance.pk)

    def perform_destroy(self, instance):
        self._invalidate_review_cache(product_id=instance.product_id, pk=instance.pk)
        instance.delete()


# ─── Helper ───────────────────────────────────────────────────────────────────

def Response_from_cache(data):
    from rest_framework.response import Response
    return Response(data)