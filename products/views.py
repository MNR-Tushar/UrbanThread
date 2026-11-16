from rest_framework import viewsets
from .serializers import *
from .models import *
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum, Count, Q
from django.db import connection
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from drf_spectacular.utils import extend_schema

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
PRODUCT_SECTIONS_CACHE_TTL = 60 * 5  # 5 minutes; best-seller totals can change after orders
CATEGORY_CACHE_TTL = 60 * 60   # 1 hour
BRAND_CACHE_TTL    = 60 * 60   # 1 hour
SIZE_COLOR_TTL     = 60 * 60 * 6  # 6 hours

@extend_schema(tags=["Products - Categories"])
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

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
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
    
    
@extend_schema(tags=["Products - Brands"])
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

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
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
        
        
@extend_schema(tags=["Products"])
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'brand').prefetch_related('productimage_set').all()
    lookup_field = 'slug'
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'brand', 'is_available']
    search_fields = ['product_name', 'description', 'brand__brand_name', 'category__category_name']
    ordering_fields = ['product_name', 'price', 'created_at', 'is_featured']
    ordering = ['-created_at']

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        term = self.request.query_params.get('search', '').strip()
        if term and connection.vendor == 'postgresql':
            vector = SearchVector('product_name', weight='A') + SearchVector('description', weight='B') + SearchVector('brand__brand_name', weight='B') + SearchVector('category__category_name', weight='C')
            query = SearchQuery(term, search_type='plain')
            ranked = queryset.annotate(_search_vector=vector, _search_rank=SearchRank(vector, query)).filter(_search_vector=query).order_by('-_search_rank')
            if ranked.exists():
                return ranked
        return queryset

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def suggest(self, request):
        query = request.query_params.get('q', '').strip()
        if len(query) < 2:
            return Response([])
        rows = Product.objects.filter(is_available=True).filter(
            Q(product_name__icontains=query) | Q(brand__brand_name__icontains=query) | Q(category__category_name__icontains=query)
        ).values('id', 'product_name', 'slug')[:8]
        return Response(list(rows))

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def related(self, request, slug=None):
        product = self.get_object()
        rows = Product.objects.filter(is_available=True).exclude(pk=product.pk).filter(
            Q(category=product.category) | Q(brand=product.brand)
        ).select_related('category', 'brand').prefetch_related('productimage_set').order_by('-is_featured', '-created_at')[:8]
        return Response(ProductListSerializer(rows, many=True, context={'request': request}).data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def sections(self, request):
        cache_key = 'product_sections'
        has_scheduled_sales = Product.objects.filter(Q(sale_starts_at__isnull=False) | Q(sale_ends_at__isnull=False)).exists()
        cached = None if has_scheduled_sales else cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        available = self.get_queryset().filter(is_available=True)
        context = {'request': request}
        data = {
            'featured': ProductListSerializer(available.filter(is_featured=True).order_by('-created_at')[:8], many=True, context=context).data,
            'new_arrivals': ProductListSerializer(available.order_by('-created_at')[:8], many=True, context=context).data,
            'best_sellers': ProductListSerializer(available.annotate(sold=Sum('orderitem__quantity')).filter(sold__gt=0).order_by('-sold')[:8], many=True, context=context).data,
        }
        if not has_scheduled_sales:
            cache.set(cache_key, data, timeout=PRODUCT_SECTIONS_CACHE_TTL)
        return Response(data)
    
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
        has_scheduled_sales = Product.objects.filter(Q(sale_starts_at__isnull=False) | Q(sale_ends_at__isnull=False)).exists()
        cached = None if has_scheduled_sales else cache.get(cache_key)
        if cached is not None:
            return Response(cached)
 
        response = super().list(request, *args, **kwargs)
        if not has_scheduled_sales:
            cache.set(cache_key, response.data, timeout=PRODUCT_CACHE_TTL)
        return response
 
    def retrieve(self, request, *args, **kwargs):
        # The product route uses ``slug`` as its lookup field, so DRF passes
        # that value in ``kwargs['slug']`` rather than ``kwargs['pk']``.
        # Using pk here made every detail request share product_detail:None.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        cache_key = _product_detail_key(kwargs.get(lookup_url_kwarg))
        has_scheduled_sales = Product.objects.filter(Q(sale_starts_at__isnull=False) | Q(sale_ends_at__isnull=False)).exists()
        cached = None if has_scheduled_sales else cache.get(cache_key)
        if cached is not None:
            return Response(cached)
 
        response = super().retrieve(request, *args, **kwargs)
        if not has_scheduled_sales:
            cache.set(cache_key, response.data, timeout=PRODUCT_CACHE_TTL)
        return response
 
    def _invalidate_product_cache(self, pk=None, slug=None):
        cache.delete('product_sections')
        # Specific product cache delete
        if pk:
            cache.delete(_product_detail_key(pk))
        if slug:
            cache.delete(_product_detail_key(slug))
        # All product list cache delete — pattern delete (django-redis)
        try:
            cache.delete_pattern("*product_list:*")
            cache.delete_pattern("*product_detail:*")
        except AttributeError:
            # django-redis < 5.0 does not support delete_pattern, fallback to clearing entire cache
            cache.clear()
 
    def perform_create(self, serializer):
        instance = serializer.save()
        self._invalidate_product_cache()
 
    def perform_update(self, serializer):
        instance = serializer.save()
        self._invalidate_product_cache(pk=instance.pk, slug=instance.slug)
 
    def perform_destroy(self, instance):
        pk = instance.pk
        slug = instance.slug
        instance.delete()
        self._invalidate_product_cache(pk=pk, slug=slug)
    
@extend_schema(tags=["Products - Images"])
class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['productimg']
    
    def perform_create(self, serializer):
        instance = serializer.save()
        cache.delete('product_sections')
        # Invalidate cache for the associated product detail and list views
        cache.delete(_product_detail_key(instance.productimg_id))
        try:
            cache.delete_pattern("*product_list:*")
            cache.delete_pattern("*product_detail:*")
        except AttributeError:
            cache.clear()

    def perform_update(self, serializer):
        instance = serializer.save()
        cache.delete('product_sections')
        cache.delete(_product_detail_key(instance.productimg_id))
        try:
            cache.delete_pattern("*product_list:*")
            cache.delete_pattern("*product_detail:*")
        except AttributeError:
            cache.clear()

    def perform_destroy(self, instance):
        product_id = instance.productimg_id
        instance.delete()
        cache.delete('product_sections')
        cache.delete(_product_detail_key(product_id))
        try:
            cache.delete_pattern("*product_list:*")
            cache.delete_pattern("*product_detail:*")
        except AttributeError:
            cache.clear()


@extend_schema(tags=["Store banners"])
class StoreBannerViewSet(viewsets.ModelViewSet):
    serializer_class = StoreBannerSerializer

    def get_queryset(self):
        queryset = StoreBanner.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


@extend_schema(tags=["Store settings"])
class StoreSettingsViewSet(viewsets.ModelViewSet):
    queryset = StoreSettings.objects.all().order_by('id')
    serializer_class = StoreSettingsSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    def create(self, request, *args, **kwargs):
        current = StoreSettings.objects.order_by('id').first()
        if current:
            serializer = self.get_serializer(current, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return super().create(request, *args, **kwargs)


@extend_schema(tags=["Wishlist"])
class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistItemSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user).select_related('product', 'product__category', 'product__brand')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item, created = WishlistItem.objects.get_or_create(user=request.user, product=serializer.validated_data['product'])
        return Response(self.get_serializer(item).data, status=201 if created else 200)


@extend_schema(tags=['Delivery zones'])
class DeliveryZoneViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryZoneSerializer

    def get_queryset(self):
        qs = DeliveryZone.objects.all()
        return qs if self.request.user.is_staff else qs.filter(is_active=True)

    def get_permissions(self):
        return [AllowAny()] if self.action in ['list', 'retrieve'] else [IsAdminUser()]
 
@extend_schema(tags=["Products - Sizes"])
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
        


@extend_schema(tags=["Products - Colors"])
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
