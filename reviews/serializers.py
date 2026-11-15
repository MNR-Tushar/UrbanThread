from rest_framework import serializers
from .models import Review, ReviewImage
from accounts.serializers import CustomUserSerializer
from products.serializers import ProductListSerializer


class ReviewSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    product_detail = ProductListSerializer(read_only=True, source='product')
    review_images = serializers.SerializerMethodField()
    images = serializers.ListField(child=serializers.ImageField(), write_only=True, required=False, max_length=5)
    helpful_count = serializers.IntegerField(source='helpful_votes.count', read_only=True)
    user_found_helpful = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user', 'product', 'product_detail', 'rating', 'review_text', 'is_approved', 'verified_purchase', 'review_images', 'images', 'helpful_count', 'user_found_helpful', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at', 'verified_purchase']

    def get_review_images(self, obj):
        return [self.context['request'].build_absolute_uri(item.image.url) for item in obj.images.all()]

    def get_user_found_helpful(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and obj.helpful_votes.filter(user=request.user).exists())

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        review = Review.objects.create(**validated_data)
        ReviewImage.objects.bulk_create([ReviewImage(review=review, image=image) for image in images])
        return review

    def update(self, instance, validated_data):
        images = validated_data.pop('images', [])
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        ReviewImage.objects.bulk_create([ReviewImage(review=instance, image=image) for image in images])
        return instance

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_product(self, value):
        if self.instance and value.pk != self.instance.product_id:
            raise serializers.ValidationError('A review cannot be moved to a different product.')
        return value

    def validate_is_approved(self, value):
        request = self.context.get('request')
        if request and not request.user.is_staff:
            raise serializers.ValidationError("Only staff can approve reviews.")
        return value
