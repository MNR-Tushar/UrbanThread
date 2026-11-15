from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet
from .return_views import ReturnRequestViewSet

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')
return_router = DefaultRouter()
return_router.register(r'', ReturnRequestViewSet, basename='return-request')

app_name = 'orders'

urlpatterns = [
    path('return-requests/', include(return_router.urls)),
    path('', include(router.urls)),
]
