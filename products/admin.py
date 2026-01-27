from django.contrib import admin
from .models import *

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id','category_name', 'created_at')
    ordering = ('-created_at',)
    search_fields = ('category_name', 'description')
    list_filter = ('created_at',)
    

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id','band_name', 'created_at')
    ordering = ('-created_at',)
    search_fields = ('band_name', 'description')
    list_filter = ('created_at',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','product_name', 'price', 'discount_price', 'is_available', 'category', 'brand')
    list_filter = ('category', 'brand')
    search_fields = ('product_name', 'description')
    ordering = ('-created_at',)
    
    
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id','productimg', 'image', 'created_at')
    ordering = ('-created_at',)
    list_filter = ('productimg', 'created_at')
    search_fields = ('product__product_name', 'product__description')
    readonly_fields = ('created_at',)
    
    
@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('id','color', 'created_at')
    ordering = ('-created_at',)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('id','size_type', 'created_at')
    ordering = ('-created_at',)