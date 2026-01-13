from django.contrib import admin
from .models import *

# Register your models here.

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'expiration_date', 'is_active')
    list_filter = ('expiration_date', 'is_active')
    search_fields = ('code',)