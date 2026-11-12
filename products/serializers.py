from rest_framework import serializers
from .models import *


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('slug', 'created_at',)


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = ('slug', 'created_at',)


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'


class StoreBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreBanner
        fields = '__all__'


class StoreSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreSettings
        fields = '__all__'
        read_only_fields = ['updated_at']


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


class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "category_name"]


class BrandMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "brand_name"]


class ProductListSerializer(serializers.ModelSerializer):
    category = CategoryMiniSerializer(read_only=True)
    brand = BrandMiniSerializer(read_only=True)
    # FIX: source was 'images' (nonexistent); correct reverse accessor is 'productimage_set'
    images = ProductImageSerializer(many=True, read_only=True, source='productimage_set')

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('created_at', 'slug')


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True, source='productimage_set')
    category_id = serializers.IntegerField(write_only=True)
    brand_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Product
        fields = ['id', 'product_name', 'sku', 'description', 'price', 'discount_price',
                  'is_available', 'slug', 'created_at', 'category', 'brand',
                  'images', 'category_id', 'brand_id','updated_at']
        read_only_fields = ['slug', 'created_at']

    def create(self, validated_data):
        return Product.objects.create(**validated_data)


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(source='product', queryset=Product.objects.all(), write_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_id', 'created_at']
        read_only_fields = ['created_at']
