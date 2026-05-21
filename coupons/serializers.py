from rest_framework import serializers
from .models import *
from datetime import date


class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'discount', 'start_date', 'expiration_date', 'is_active', 'is_valid']

    def get_is_valid(self, obj):
        today = date.today()
        if obj.start_date and obj.start_date > today:
            return False
        return obj.expiration_date >= today and obj.is_active
    
class CouponValidationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=10)
    

