from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import logging
import re
import secrets
import requests
from rest_framework import status, viewsets
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view

from .serializers import *
from .models import Profile, Address, PasswordResetOTP
from .tasks import send_welcome_email
User = get_user_model()
logger = logging.getLogger(__name__)


def _find_reset_user(contact, channel):
    if channel == 'email':
        return User.objects.filter(email__iexact=contact, is_active=True).first()
    digits = re.sub(r'\D', '', contact)
    candidates = {contact.strip(), digits, f'+{digits}'}
    if digits.startswith('01'):
        candidates.add(f'+88{digits}')
    elif digits.startswith('8801'):
        candidates.add(f'+{digits}')
    return User.objects.filter(
        Q(phone__in=candidates) | Q(profile__phone__in=candidates), is_active=True,
    ).distinct().first()


def _deliver_reset_otp(user, channel, code):
    expiry_minutes = 10
    message = f'Your UrbanThread password reset code is {code}. It expires in {expiry_minutes} minutes.'
    if channel == 'email':
        EmailMultiAlternatives(
            'Your UrbanThread password reset code',
            f'Hi {user.first_name or user.username},\n\n{message}\n\nIf you did not request this, ignore this email.',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        ).send(fail_silently=False)
        return

    gateway_url = getattr(settings, 'SMS_API_URL', '')
    gateway_token = getattr(settings, 'SMS_API_TOKEN', '')
    phone = user.phone or getattr(getattr(user, 'profile', None), 'phone', '')
    if not gateway_url or not gateway_token or not phone:
        raise RuntimeError('Phone OTP gateway is not configured.')
    response = requests.post(
        gateway_url,
        json={'to': phone, 'message': message, 'sender': getattr(settings, 'SMS_SENDER_ID', '')},
        headers={'Authorization': f'Bearer {gateway_token}'},
        timeout=10,
    )
    response.raise_for_status()


class PasswordResetRequestView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetRequestSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'password_reset_request'

    @extend_schema(tags=['Accounts - Password'])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.validated_data['contact']
        channel = serializer.validated_data['channel']
        user = _find_reset_user(contact, channel)
        if user:
            now = timezone.now()
            PasswordResetOTP.objects.filter(user=user, channel=channel, consumed_at__isnull=True).update(consumed_at=now)
            code = f'{secrets.randbelow(1_000_000):06d}'
            otp = PasswordResetOTP.objects.create(
                user=user,
                channel=channel,
                code_hash=make_password(code),
                expires_at=now + timedelta(minutes=10),
            )
            try:
                _deliver_reset_otp(user, channel, code)
            except Exception:
                otp.consumed_at = timezone.now()
                otp.save(update_fields=['consumed_at'])
                logger.exception('Could not deliver password reset OTP via %s', channel)
                return Response({'error': 'Could not send a reset code. Check the email or SMS gateway configuration and try again.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'detail': 'If an active account matches those details, a reset code has been sent.'})


class PasswordResetConfirmView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetConfirmSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'password_reset_confirm'

    @extend_schema(tags=['Accounts - Password'])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = _find_reset_user(data['contact'], data['channel'])
        if not user:
            return Response({'error': 'The reset code is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                otp = PasswordResetOTP.objects.select_for_update().filter(
                    user=user, channel=data['channel'], consumed_at__isnull=True,
                ).order_by('-created_at').first()
                if not otp or otp.expires_at <= timezone.now() or otp.attempts >= 5:
                    return Response({'error': 'The reset code is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)
                if not check_password(data['otp'], otp.code_hash):
                    otp.attempts += 1
                    otp.save(update_fields=['attempts'])
                    return Response({'error': 'The reset code is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    validate_password(data['new_password'], user)
                except DjangoValidationError as exc:
                    return Response({'new_password': list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)
                user.set_password(data['new_password'])
                user.save(update_fields=['password'])
                otp.consumed_at = timezone.now()
                otp.save(update_fields=['consumed_at'])
                PasswordResetOTP.objects.filter(user=user, consumed_at__isnull=True).update(consumed_at=timezone.now())
        except Exception:
            logger.exception('Password reset failed')
            raise
        return Response({'detail': 'Password reset successfully. You can now sign in.'})


class ChangePasswordView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'password_change'

    @extend_schema(tags=['Accounts - Password'])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            validate_password(serializer.validated_data['new_password'], request.user)
        except DjangoValidationError as exc:
            return Response({'new_password': list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        return Response({'detail': 'Password changed successfully.'})

class UserRegisterationAPIView(GenericAPIView):
    """
    An endpoint for the client to create a new User.
    """

    permission_classes = (AllowAny,)
    serializer_class =UserRegisterationSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'register'

    @extend_schema(tags=["Accounts - Register"])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        try:
            send_welcome_email.delay(user.pk)
        except Exception as e:
            logger.error("Failed to send welcome email for user %s: %s", user.pk, e)    
        token = RefreshToken.for_user(user)
        data = serializer.data
        data["tokens"] = {"refresh": str(token), "access": str(token.access_token)}
        return Response(data, status=status.HTTP_201_CREATED)

class UserLoginAPIView(GenericAPIView):
    """
    An endpoint to authenticate existing users using their email and password.
    """

    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'login'
    
    @extend_schema(tags=["Accounts - Login"])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        serializer = CustomUserSerializer(user)
        token = RefreshToken.for_user(user)
        data = serializer.data
        data["tokens"] = {"refresh": str(token), "access": str(token.access_token)}
        return Response(data, status=status.HTTP_200_OK)

class UserLogoutAPIView(GenericAPIView):
    """
    An endpoint to logout users.
    """

    permission_classes = (IsAuthenticated,)

    @extend_schema(tags=["Accounts - Login"])
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
@extend_schema_view(
    list=extend_schema(tags=["Accounts - Users"]),
    create=extend_schema(tags=["Accounts - Users"]),
    retrieve=extend_schema(tags=["Accounts - Users"]),
    update=extend_schema(tags=["Accounts - Users"]),
    partial_update=extend_schema(tags=["Accounts - Users"]),
    destroy=extend_schema(tags=["Accounts - Users"]),
)
class Userviewset(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()

    def get_object(self):
        if self.request.user.is_staff and self.kwargs.get(self.lookup_field) != 'me':
            return super().get_object()
        return self.request.user
    
    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return User.objects.all()

        return User.objects.filter(id=user.id)


@extend_schema_view(
    list=extend_schema(tags=["Accounts - Profile"]),
    create=extend_schema(tags=["Accounts - Profile"]),
    retrieve=extend_schema(tags=["Accounts - Profile"]),
    update=extend_schema(tags=["Accounts - Profile"]),
    partial_update=extend_schema(tags=["Accounts - Profile"]),
    destroy=extend_schema(tags=["Accounts - Profile"]),
)
class ProfileViewset(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer
    
    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return Profile.objects.all()

        return Profile.objects.filter(user=user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    

@extend_schema_view(
    list=extend_schema(tags=["Accounts - Address"]),
    create=extend_schema(tags=["Accounts - Address"]),
    retrieve=extend_schema(tags=["Accounts - Address"]),
    update=extend_schema(tags=["Accounts - Address"]),
    partial_update=extend_schema(tags=["Accounts - Address"]),
    destroy=extend_schema(tags=["Accounts - Address"]),
)
class AddressViewset(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = AddressSerializer
    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return Address.objects.all()

        return Address.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
