from django.contrib import admin
from .models import *

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'size', 'quantity', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_filter = ('product', 'color', 'size', 'created_at', 'updated_at')
    search_fields = ('product__name', 'color__name', 'size__name')
