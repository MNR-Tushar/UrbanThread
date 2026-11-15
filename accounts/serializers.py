from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import *

class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize CustomUser model.
    """

    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "first_name", "last_name", "phone", "address", "is_staff", "is_superuser", "is_active", "date_joined")
        read_only_fields = ("is_staff", "is_superuser", "date_joined")

    def validate_is_active(self, value):
        if not self.context['request'].user.is_staff:
            raise serializers.ValidationError("Only staff can change account access.")
        return value

class UserRegisterationSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize registration requests and create a new user.
    """

    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer class to authenticate users with email and password.
    """

    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")


class PasswordResetRequestSerializer(serializers.Serializer):
    contact = serializers.CharField(max_length=254)
    channel = serializers.ChoiceField(choices=['email', 'phone'])

    def validate_contact(self, value):
        return value.strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    contact = serializers.CharField(max_length=254)
    channel = serializers.ChoiceField(choices=['email', 'phone'])
    otp = serializers.RegexField(r'^\d{6}$')
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=8)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=8)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({'current_password': 'Current password is incorrect.'})
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs
    
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields ='__all__'
        read_only_fields = ("user", "created_at", "updated_at")
        
        
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'user', 'full_name', 'city', 'state', 'pincode', 'phone', 'address']
        read_only_fields = ['user']
