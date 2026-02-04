from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')

app_name = 'payments'

urlpatterns = [
    path('', include(router.urls)),
    
    # Payment initiation
    path('initiate/', InitiatePaymentView.as_view(), name='initiate-payment'),
    
    # SSL Commerce callbacks
    path('sslcommerz/success/', SSLCommerzSuccessView.as_view(), name='sslcommerz-success'),
    path('sslcommerz/fail/', SSLCommerzFailView.as_view(), name='sslcommerz-fail'),
    path('sslcommerz/cancel/', SSLCommerzCancelView.as_view(), name='sslcommerz-cancel'),
    path('sslcommerz/ipn/', SSLCommerzIPNView.as_view(), name='sslcommerz-ipn'),
    
    # Refund
    path('refund/', RefundPaymentView.as_view(), name='refund-payment'),
]