from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'review_text', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_filter = ('user', 'product', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'product__name')