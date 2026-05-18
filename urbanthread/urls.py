
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="UrbanThread API",
        default_version='v1',
        description="API documentation for UrbanThread",
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('inventory/', include('inventory.urls')),
    path('inventorys/', include('inventory.urls')),
    path('cart/', include('cart.urls')),
    path('coupons/', include('coupons.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('reviews/', include('reviews.urls')),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
