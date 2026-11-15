from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'allusers', Userviewset, basename='user')
router.register(r'address', AddressViewset, basename='address')
router.register(r'profile', ProfileViewset, basename='profile')
app_name = "accounts"

urlpatterns = [
    path("register/", UserRegisterationAPIView.as_view(), name="create-user"),
    path("login/", UserLoginAPIView.as_view(), name="login-user"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", UserLogoutAPIView.as_view(), name="logout-user"),
    path("password/reset/request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("password/change/", ChangePasswordView.as_view(), name="password-change"),
    path("email/verification/resend/", EmailVerificationResendView.as_view(), name="email-verification-resend"),
    path("email/verification/confirm/", EmailVerificationConfirmView.as_view(), name="email-verification-confirm"),
    path("google/", GoogleSignInView.as_view(), name="google-sign-in"),
    path("", include(router.urls)),

]
