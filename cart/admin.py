from django.contrib import admin
from .models import *

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_filter = ('user', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'color', 'size', 'quantity', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_filter = ('cart', 'product', 'color', 'size', 'created_at', 'updated_at')
    search_fields = ('cart__user__email', 'product__name', 'color__name', 'size__name')