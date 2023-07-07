from typing import Any

from django.db import transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import filters, generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response

from config.settings.base import CACHE_DURATION
from uia_backend.accounts.api.v1.serializers import (
    ChangePasswordSerializer,
    CustomUserSerializer,
    EmailVerificationSerializer,
    FollowsSerializer,
    FollowerCountSerializer,
    FollowingCountSerializer,
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
from uia_backend.accounts.models import (
    CustomUser,
    Follows,
    FriendShipInvitation,
    UserFriendShipSettings,
)

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


class FollowAPIView(generics.CreateAPIView):
    serializer_class = FollowsSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["post"]

    @transaction.atomic()
    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "info": "Success",
                    "message": "You followed John Doe successfully.",
                },
            )
        ]
    )
    def post(self, request, *args, **kwargs) -> Response:
        """Follow a user by id"""

        user_from = request.user
        user_to = kwargs.get("user_id")
        data = {"user_from": user_from.id, "user_to": user_to}

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_to = serializer.validated_data['user_to']

        return Response(
            {
                "info": "Success",
                "message": f"You followed {user_to.get_full_name()} successfully.",
            },
            status=status.HTTP_200_OK,
        )


class UnFollowAPIView(generics.DestroyAPIView):
    serializer_class = FollowsSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["delete"]

    @transaction.atomic()
    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "info": "Success",
                    "message": "You unfollowed John Doe successfully.",
                },
            )
        ]
    )
    def delete(self, request, *args, **kwargs) -> Response:
        """Unfollow a user by id"""

        user_from = request.user
        user_to = kwargs.get("user_id")
        data = {"user_from": user_from.id, "user_to": user_to}

        serializer = self.get_serializer(data=data)
        instance = serializer.get_followership(attrs=data)
        self.perform_destroy(instance)

        user_to = instance.user_to

        return Response(
            {
                "info": "Success",
                "message": f"You unfollowed {user_to.get_full_name()} successfully.",
            },
            status=status.HTTP_200_OK,
        )


class FollowerCountAPIView(generics.RetrieveAPIView):
    serializer_class = FollowerCountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        return Follows.objects.filter(user_to=user.id)

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
                        "follower_count": 3,
                    },
                },
            )
        ]
    ) 
    def get(self, request, *args, **kwargs) -> Response:
        """Retrieve a user follower's count by id"""

        followers = self.get_object()
        followers_count = followers.count()
        serializer = self.get_serializer({"follower_count": followers_count})

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class FollowingCountAPIView(generics.RetrieveAPIView):
    serializer_class = FollowingCountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        return Follows.objects.filter(user_from=user.id)

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
                        "following_count": 3,
                    },
                },
            )
        ]
    ) 
    def get(self, request, *args, **kwargs) -> Response:
        """Retrieve a user following's count by id"""

        following = self.get_object()
        following_count = following.count()
        serializer = self.get_serializer({"following_count": following_count})

        return Response(data=serializer.data, status=status.HTTP_200_OK)


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


class UserProfileListView(generics.ListAPIView):
    queryset = CustomUser.objects.filter(is_active=True)
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["first_name", "last_name"]

    @method_decorator(cache_page(CACHE_DURATION))
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)


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


class UserProfileSearchView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.kwargs.get("name")
        queryset = queryset.filter(
            Q(first_name__startswith=name) | Q(last_name__startswith=name)
        ).distinct()
        return queryset

    @method_decorator(cache_page(CACHE_DURATION))
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)
