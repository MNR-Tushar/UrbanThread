from rest_framework import serializers
from .models import *
from datetime import date


class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'discount', 'expiration_date', 'is_active', 'is_valid']

    def get_is_valid(self, obj):
        return obj.expiration_date >= date.today()
    
class CouponValidationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=10)
    

