from django.contrib.auth import get_user_model
import logging
from rest_framework import status, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view

from .serializers import *
from .models import Profile, Address
from .tasks import send_welcome_email
User = get_user_model()
logger = logging.getLogger(__name__)

class UserRegisterationAPIView(GenericAPIView):
    """
    An endpoint for the client to create a new User.
    """

    permission_classes = (AllowAny,)
    serializer_class =UserRegisterationSerializer

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
