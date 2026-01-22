from rest_framework import serializers
from .models import *

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('slug','created_at',)
        
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = ('slug','created_at',)

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'
        read_only_fields = ('created_at',)

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'
        read_only_fields = ('created_at',)

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = '__all__'
        read_only_fields = ('created_at',)

class ProductListSerializer(serializers.ModelSerializer):
    category=CategorySerializer(read_only=True)
    brand=BrandSerializer(read_only=True)
    images=ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields ='__all__'
        read_only_fields = ('created_at','slug')
        
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True, source='productimage_set')
    category_id = serializers.IntegerField(write_only=True)
    brand_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'discount_price', 
                  'is_available', 'slug', 'created_at', 'category', 'brand', 
                  'images', 'category_id', 'brand_id']
        read_only_fields = ['slug', 'created_at']
    
    def create(self, validated_data):
        return Product.objects.create(**validated_data)