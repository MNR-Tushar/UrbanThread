from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductListSerializer, ColorSerializer, SizeSerializer
from inventory.models import Inventory


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    color = ColorSerializer(read_only=True)
    size = SizeSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    color_id = serializers.IntegerField(write_only=True)
    size_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'color', 'size', 'quantity',
                  'product_id', 'color_id', 'size_id', 'subtotal',
                  'created_at', 'updated_at']
        read_only_fields = ['cart', 'created_at', 'updated_at']
    
    def get_subtotal(self, obj):
        price = obj.product.discount_price if obj.product.discount_price > 0 else obj.product.price
        return float(price * obj.quantity)
    
    def validate(self, data):
        product_id = data.get('product_id')
        color_id = data.get('color_id')
        size_id = data.get('size_id')
        quantity = data.get('quantity', 1)
        
        # Check inventory
        try:
            inventory = Inventory.objects.get(
                product_id=product_id,
                color_id=color_id,
                size_id=size_id
            )
            if inventory.quantity < quantity:
                raise serializers.ValidationError(
                    f"Only {inventory.quantity} items available in stock"
                )
        except Inventory.DoesNotExist:
            raise serializers.ValidationError("Product variant not available")
        
        return data


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True, source='cartitem_set')
    total_items = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_items', 'total_amount',
                  'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_total_items(self, obj):
        return obj.cartitem_set.count()
    
    def get_total_amount(self, obj):
        total = 0
        for item in obj.cartitem_set.all():
            price = item.product.discount_price if item.product.discount_price > 0 else item.product.price
            total += price * item.quantity
        return float(total)