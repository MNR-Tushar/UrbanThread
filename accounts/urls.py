from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'allusers', Userviewset, basename='user')
app_name = "accounts"

urlpatterns = [
    path("register/", UserRegisterationAPIView.as_view(), name="create-user"),
    path("login/", UserLoginAPIView.as_view(), name="login-user"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", UserLogoutAPIView.as_view(), name="logout-user"),
    path("", include(router.urls)),

]