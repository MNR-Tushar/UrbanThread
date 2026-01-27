from rest_framework import serializers
from .models import Inventory
from products.serializers import *


class InventorySerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    color = ColorSerializer(read_only=True)
    size = SizeSerializer(read_only=True)
    
    product_id = serializers.IntegerField(write_only=True)
    color_id = serializers.IntegerField(write_only=True)
    size_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Inventory
        fields = ['product', 'color', 'size', 'quantity', 'product_id', 'color_id', 'size_id', 'created_at', 'updated_at']
        read_only_fields = ('created_at', 'updated_at')