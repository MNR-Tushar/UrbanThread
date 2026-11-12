from rest_framework import serializers
from .models import Review
from accounts.serializers import CustomUserSerializer
from products.serializers import ProductListSerializer


class ReviewSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    product_detail = ProductListSerializer(read_only=True, source='product')

    class Meta:
        model = Review
        fields = ['id', 'user', 'product', 'product_detail', 'rating', 'review_text', 'is_approved', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_is_approved(self, value):
        request = self.context.get('request')
        if request and not request.user.is_staff:
            raise serializers.ValidationError("Only staff can approve reviews.")
        return value
