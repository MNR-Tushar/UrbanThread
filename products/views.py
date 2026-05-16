from rest_framework import viewsets
from .serializers import *
from .models import *
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.core.cache import cache
from rest_framework.response import Response

# ─── Cache Key Helpers ────────────────────────────────────────────────────────
 
def _product_list_key(params: str) -> str:
    return f"product_list:{params}"
 
def _product_detail_key(pk) -> str:
    return f"product_detail:{pk}"
 
def _category_list_key() -> str:
    return "category_list"
 
def _brand_list_key() -> str:
    return "brand_list"
 
def _size_list_key() -> str:
    return "size_list"
 
def _color_list_key() -> str:
    return "color_list"


PRODUCT_CACHE_TTL  = 60 * 15   # 15 minutes
CATEGORY_CACHE_TTL = 60 * 60   # 1 hour
BRAND_CACHE_TTL    = 60 * 60   # 1 hour
SIZE_COLOR_TTL     = 60 * 60 * 6  # 6 hours

class CategoryViewset(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category_name']
    search_fields = ['category_name', 'description']
    ordering_fields = ['category_name', 'created_at']
    ordering = ['-created_at']
    
    def list(self, request, *args, **kwargs):
        cache_key = _category_list_key()
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, CATEGORY_CACHE_TTL)
        return response
    
    def _invalidate_cache(self):
        cache.delete(_category_list_key())
 
    def perform_create(self, serializer):
        serializer.save()
        self._invalidate_cache()
 
    def perform_update(self, serializer):
        serializer.save()
        self._invalidate_cache()
 
    def perform_destroy(self, instance):
        instance.delete()
        self._invalidate_cache()
    
    
class BrandViewset(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['brand_name']
    search_fields = ['brand_name', 'description']
    ordering_fields = ['brand_name', 'created_at']
    ordering = ['-created_at']
    
    def list(self, request, *args, **kwargs):
        cache_key = _brand_list_key()
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
 
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=BRAND_CACHE_TTL)
        return response
 
    def _invalidate_cache(self):
        cache.delete(_brand_list_key())
 
    def perform_create(self, serializer):
        serializer.save()
        self._invalidate_cache()
 
    def perform_update(self, serializer):
        serializer.save()
        self._invalidate_cache()
 
    def perform_destroy(self, instance):
        instance.delete()
        self._invalidate_cache()
        
        
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'brand').all()
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'brand', 'is_available']
    search_fields = ['product_name', 'description']
    ordering_fields = ['product_name', 'price', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    def list(self, request, *args, **kwargs):
        # Cache key should reflect all query params for accurate caching
        params = request.query_params.urlencode()
        cache_key = _product_list_key(params)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
 
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=PRODUCT_CACHE_TTL)
        return response
 
    def retrieve(self, request, *args, **kwargs):
        cache_key = _product_detail_key(kwargs.get('pk'))
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
 
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=PRODUCT_CACHE_TTL)
        return response
 
    def _invalidate_product_cache(self, pk=None):
        # Specific product cache delete
        if pk:
            cache.delete(_product_detail_key(pk))
        # All product list cache delete — pattern delete (django-redis)
        try:
            cache.delete_pattern("*product_list:*")
        except AttributeError:
            # django-redis < 5.0 does not support delete_pattern, fallback to clearing entire cache
            cache.clear()
 
    def perform_create(self, serializer):
        instance = serializer.save()
        self._invalidate_product_cache()
 
    def perform_update(self, serializer):
        instance = serializer.save()
        self._invalidate_product_cache(pk=instance.pk)
 
    def perform_destroy(self, instance):
        pk = instance.pk
        instance.delete()
        self._invalidate_product_cache(pk=pk)
    
class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['productimg']
    
    def perform_create(self, serializer):
        instance = serializer.save()
        # Invalidate cache for the associated product detail and list views
        cache.delete(_product_detail_key(instance.productimg_id))
        try:
            cache.delete_pattern("*product_list:*")
        except AttributeError:
            pass
 
    def perform_destroy(self, instance):
        pk = instance.productimg_id
        instance.delete()
        cache.delete(_product_detail_key(pk))
        try:
            cache.delete_pattern("*product_list:*")
        except AttributeError:
            pass

class SizeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        cache_key = _size_list_key()
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
 
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=SIZE_COLOR_TTL)
        return response
        


class ColorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        cache_key = _color_list_key()
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
 
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=SIZE_COLOR_TTL)
        return response