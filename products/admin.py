from django.contrib import admin
from .models import *

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    ordering = ('-created_at',)
    search_fields = ('name', 'description')
    list_filter = ('created_at',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'discount_price', 'is_available', 'category', 'brand')
    list_filter = ('category', 'brand')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    
    
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image', 'created_at')
    ordering = ('-created_at',)
    list_filter = ('product', 'created_at')
    search_fields = ('product__name', 'product__description')
    readonly_fields = ('created_at',)
    
    
@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    ordering = ('-created_at',)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    ordering = ('-created_at',)