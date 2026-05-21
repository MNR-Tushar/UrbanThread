from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache
from drf_spectacular.utils import extend_schema

from .serializers import InventorySerializer
from .models import Inventory


# ─── Cache Key Helpers ────────────────────────────────────────────────────────

def _inventory_list_key(params: str) -> str:
    return f"inventory_list:{params}"

def _inventory_detail_key(pk) -> str:
    return f"inventory_detail:{pk}"

def _availability_key(product_id, color_id, size_id) -> str:
    return f"inventory_avail:{product_id}:{color_id}:{size_id}"

def _product_inventory_key(product_id) -> str:
    return f"product_inventory:{product_id}"


INVENTORY_CACHE_TTL     = 60 * 10   # 10 minutes
AVAILABILITY_CACHE_TTL  = 60 * 5    # 5 minutes


@extend_schema(tags=["Inventory - List & Detail"])
class InventoryViewset(viewsets.ModelViewSet):
    queryset = Inventory.objects.select_related('product', 'color', 'size').all()
    serializer_class = InventorySerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'size', 'color']
    search_fields = ['product__product_name', 'size__size_type', 'color__color']
    ordering_fields = ['product', 'size', 'color', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'check_availability', 'product_inventory']:
            return [AllowAny()]
        return [IsAdminUser()]

    # ─── List ─────────────────────────────────────────────────────────────────

    def list(self, request, *args, **kwargs):
        params = request.query_params.urlencode()
        cache_key = _inventory_list_key(params)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=INVENTORY_CACHE_TTL)
        return response

    # ─── Retrieve ─────────────────────────────────────────────────────────────

    def retrieve(self, request, *args, **kwargs):
        cache_key = _inventory_detail_key(kwargs.get('pk'))
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=INVENTORY_CACHE_TTL)
        return response

    # ─── Cache Invalidation ───────────────────────────────────────────────────

    def _invalidate_inventory_cache(self, instance=None):
        if instance:
            cache.delete(_inventory_detail_key(instance.pk))
            cache.delete(_availability_key(instance.product_id, instance.color_id, instance.size_id))
            cache.delete(_product_inventory_key(instance.product_id))
        try:
            cache.delete_pattern("*inventory_list:*")
        except AttributeError:
            pass

    def perform_create(self, serializer):
        instance = serializer.save()
        self._invalidate_inventory_cache(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._invalidate_inventory_cache(instance)

    def perform_destroy(self, instance):
        self._invalidate_inventory_cache(instance)
        instance.delete()

    # ─── Custom Actions ───────────────────────────────────────────────────────

    @extend_schema(tags=["Inventory - Availability"])
    @action(detail=False, methods=['get'])
    def check_availability(self, request):
        product_id = request.query_params.get('product_id')
        color_id   = request.query_params.get('color_id')
        size_id    = request.query_params.get('size_id')

        if not all([product_id, color_id, size_id]):
            return Response(
                {'error': 'Missing required parameters: product_id, color_id, size_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cache_key = _availability_key(product_id, color_id, size_id)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        try:
            inventory = Inventory.objects.get(
                product_id=product_id,
                color_id=color_id,
                size_id=size_id
            )
            serializer = self.get_serializer(inventory)
            data = {
                'available': inventory.quantity > 0,
                'quantity': inventory.quantity,
                'inventory': serializer.data
            }
        except Inventory.DoesNotExist:
            data = {'available': False, 'quantity': 0}

        cache.set(cache_key, data, timeout=AVAILABILITY_CACHE_TTL)
        return Response(data)

    @action(detail=False, methods=['get'])
    def product_inventory(self, request):
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cache_key = _product_inventory_key(product_id)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        inventory = Inventory.objects.filter(product_id=product_id).select_related('product', 'color', 'size')
        serializer = self.get_serializer(inventory, many=True)
        cache.set(cache_key, serializer.data, timeout=INVENTORY_CACHE_TTL)
        return Response(serializer.data)
