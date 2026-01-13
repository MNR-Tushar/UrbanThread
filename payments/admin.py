from django.contrib import admin
from .models import *

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'order', 'payment_method', 'tranction_id', 'status', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_filter = ('user', 'order', 'payment_method', 'status', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'order__order_number')


