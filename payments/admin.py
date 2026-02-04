from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Payment, PaymentLog
import json


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'user_link', 'order_link', 'amount',
        'payment_method_display', 'status_badge', 'created_at'
    )
    list_filter = (
        'status', 'payment_method', 'currency', 'created_at',
        'card_type', 'risk_level'
    )
    search_fields = (
        'transaction_id', 'user__email', 'user__username',
        'order__order_number', 'bank_tran_id', 'val_id'
    )
    readonly_fields = (
        'user', 'order', 'transaction_id', 'val_id', 'bank_tran_id',
        'card_type', 'card_no', 'card_issuer', 'card_brand',
        'card_issuer_country', 'risk_level', 'risk_title',
        'created_at', 'updated_at', 'completed_at',
        'formatted_response_data'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'order', 'transaction_id', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'amount', 'currency', 'completed_at')
        }),
        ('SSL Commerce Details', {
            'fields': (
                'val_id', 'bank_tran_id', 'card_type', 'card_no',
                'card_issuer', 'card_brand', 'card_issuer_country'
            ),
            'classes': ('collapse',)
        }),
        ('Risk Assessment', {
            'fields': ('risk_level', 'risk_title'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('error_message', 'formatted_response_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'User'
    
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Order'
    
    def payment_method_display(self, obj):
        return obj.get_payment_method_display()
    payment_method_display.short_description = 'Payment Method'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'processing': '#007bff',
            'completed': '#28a745',
            'failed': '#dc3545',
            'refunded': '#6c757d',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def formatted_response_data(self, obj):
        if obj.response_data:
            formatted = json.dumps(obj.response_data, indent=2)
            return format_html('<pre>{}</pre>', formatted)
        return '-'
    formatted_response_data.short_description = 'Response Data'
    
    def has_add_permission(self, request):
        # Payments should only be created through the API
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only allow deletion of failed/cancelled payments
        if obj and obj.status in ['completed', 'refunded']:
            return False
        return super().has_delete_permission(request, obj)
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def mark_as_completed(self, request, queryset):
        for payment in queryset:
            if payment.status == 'pending':
                payment.mark_as_completed()
        self.message_user(request, f'{queryset.count()} payments marked as completed.')
    mark_as_completed.short_description = 'Mark selected as completed'
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='failed')
        self.message_user(request, f'{updated} payments marked as failed.')
    mark_as_failed.short_description = 'Mark selected as failed'


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'payment_link', 'event_type', 'ip_address', 'created_at'
    )
    list_filter = ('event_type', 'created_at')
    search_fields = (
        'payment__transaction_id', 'event_type', 'ip_address'
    )
    readonly_fields = (
        'payment', 'event_type', 'formatted_event_data',
        'ip_address', 'user_agent', 'created_at'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Log Information', {
            'fields': ('payment', 'event_type', 'created_at')
        }),
        ('Event Data', {
            'fields': ('formatted_event_data',)
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def payment_link(self, obj):
        url = reverse('admin:payments_payment_change', args=[obj.payment.id])
        return format_html('<a href="{}">{}</a>', url, obj.payment.transaction_id)
    payment_link.short_description = 'Payment'
    
    def formatted_event_data(self, obj):
        if obj.event_data:
            formatted = json.dumps(obj.event_data, indent=2)
            return format_html('<pre style="max-height: 400px; overflow: auto;">{}</pre>', formatted)
        return '-'
    formatted_event_data.short_description = 'Event Data'
    
    def has_add_permission(self, request):
        # Logs are automatically created
        return False
    
    def has_change_permission(self, request, obj=None):
        # Logs should not be editable
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete logs
        return request.user.is_superuser