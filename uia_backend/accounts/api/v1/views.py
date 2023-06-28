from typing import Any

from django.db import transaction
from django.db.models.query import Q, QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response

from uia_backend.accounts.api.v1.serializers import (
    ChangePasswordSerializer,
    EmailVerificationSerializer,
    FriendshipInvitationSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    RestPasswordRequestSerializer,
    UserFriendShipSettingsSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    VerifyResetPasswordOTPSerializer,
)
from uia_backend.accounts.api.v1.throttles import PasswordRestThrottle
from uia_backend.accounts.models import FriendShipInvitation, UserFriendShipSettings


class UserRegistrationAPIView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @transaction.atomic()
    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "info": "Success",
                    "code": 201,
                    "data": {
                        "first_name": "string",
                        "last_name": "string",
                        "email": "user@example.com",
                        "faculty": "string",
                        "department": "string",
                        "year_of_graduation": "2001",
                    },
                },
            )
        ]
    )
    def post(self, request: Request, *args: Any, **kwargs: dict[str, Any]) -> Response:
        return super().post(request, *args, **kwargs)


# NOTE: For now lets use a API request for this later we can build a nice looking template
# NOTE: We also have to figure out a way to handle verification for web
# (we may want to redirect to the web app or something)
class EmailVerificationAPIView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.AllowAny]

    @transaction.atomic()
    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "info": "Success",
                    "message": "Your account has been successfully verified.",
                },
            )
        ]
    )
    def get(self, request: Request, signature: str) -> Response:
        serializer = self.get_serializer(data={"signature": signature})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data)


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "put"]

    def get_object(self) -> Any:
        return self.request.user

    @transaction.atomic()
    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "info": "Success",
                    "code": 200,
                    "data": {
                        "first_name": "string",
                        "last_name": "string",
                        "faculty": "string",
                        "department": "string",
                        "year_of_graduation": "2001",
                        "bio": "string",
                        "display_name": "string",
                        "phone_number": "string",
                        "cover_photo": "string",
                        "profile_picture": "string",
                        "gender": "string",
                    },
                },
            )
        ]
    )
    def put(self, request, *args, **kwargs) -> Response:
        """Subsequent updates to the user profile"""
        return super().put(request, *args, **kwargs)

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "info": "Success",
                    "code": 200,
                    "data": {
                        "first_name": "string",
                        "last_name": "string",
                        "profile_picture": "path/image.png",
                        "cover_photo": "path/image.png",
                        "phone_number": "string",
                        "display_name": "string",
                        "year_of_graduation": "1990",
                        "department": "string",
                        "faculty": "Science",
                        "bio": "string",
                        "gender": "string",
                        "date_of_birth": "2000-10-08",
                    },
                },
            )
        ]
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)


class ChangePasswordAPIView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["put"]

    def get_object(self) -> Any:
        return self.request.user

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "code": 201,
                    "info": "Success",
                    "message": "Password Changed Successfully.",
                },
            )
        ]
    )
    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().put(request, *args, **kwargs)


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 200,
                    "data": {"auth_token": "jwt-token-asasasas"},
                },
            )
        ]
    )
    def post(self, request: Request) -> Response:
        """User login view."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # NOTE: we can send a task here to store login attempt
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class ResetPasswordRequestAPIView(generics.CreateAPIView):
    serializer_class = RestPasswordRequestSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordRestThrottle]


class VerifyResetPasswordAPIView(generics.GenericAPIView):
    """View for verifying a password reset attempt using an OTP."""

    serializer_class = VerifyResetPasswordOTPSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["post"]

    def post(self, request: Request) -> Response:
        """Verify password view."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ResetPasswordAPIView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["post"]

    def post(self, request: Request) -> Response:
        """Reset password view."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class FriendShipInvitationListAPIView(generics.ListCreateAPIView):
    serializer_class = FriendshipInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[FriendShipInvitation]:
        return FriendShipInvitation.objects.filter(
            Q(created_by=self.request.user) | Q(user=self.request.user)
        ).select_related("user", "created_by")

    def perform_create(self, serializer: FriendshipInvitationSerializer) -> None:
        serializer.save(created_by=self.request.user)


class FriendShipInvitationDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = FriendshipInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch"]

    def get_queryset(self) -> QuerySet[FriendShipInvitation]:
        return FriendShipInvitation.objects.filter(
            Q(created_by=self.request.user) | Q(user=self.request.user)
        ).select_related("user", "created_by")

    def get_object(self) -> FriendShipInvitation:
        """Get object"""
        try:
            record = FriendShipInvitation.objects.filter(
                Q(created_by=self.request.user) | Q(user=self.request.user)
            ).get(id=self.kwargs["pk"])
        except FriendShipInvitation.DoesNotExist:
            raise Http404

        return record


class UserFriendShipsListAPIView(generics.ListAPIView):
    serializer_class = UserFriendShipSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[UserFriendShipSettings]:
        return UserFriendShipSettings.objects.filter(user=self.request.user)


class UserFriendShipsDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserFriendShipSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[UserFriendShipSettings]:
        return UserFriendShipSettings.objects.filter(user=self.request.user)

    def perform_destroy(self, instance: UserFriendShipSettings) -> None:
        instance.friendship.delete()

    def get_object(self) -> UserFriendShipSettings:
        """Get object"""
        return get_object_or_404(
            UserFriendShipSettings,
            id=self.kwargs["pk"],
            user=self.request.user,
        )
