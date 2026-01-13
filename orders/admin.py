from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'total_amount', 'payment_status', 'order_status', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_filter = ('user', 'payment_status', 'order_status', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'color', 'size', 'quantity', 'price', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_filter = ('order', 'product', 'color', 'size', 'created_at', 'updated_at')
    search_fields = ('order__order_number', 'product__name', 'color__name', 'size__name')
    