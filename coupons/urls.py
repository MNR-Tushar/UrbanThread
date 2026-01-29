from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'', CouponViewset, basename='coupon')

app_name = 'coupons'

urlpatterns = [
    path('', include(router.urls)),
]