from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'inventorys', InventoryViewset, basename='inventory')

app_name = 'inventory'

urlpatterns = [
    path('', include(router.urls)),
]