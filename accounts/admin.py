from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

from .models import CustomUser

admin.site.register(CustomUser, UserAdmin)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'state', 'pincode', 'phone', 'address', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_filter = ('user', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')



@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'image', 'phone', 'gender', 'date_of_birth', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_filter = ('user', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')