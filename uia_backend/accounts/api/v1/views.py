from typing import Any

from django.db import transaction
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response

from uia_backend.accounts.api.v1.serializers import (
    ChangePasswordSerializer,
    CustomUserSerializer,
    EmailVerificationSerializer,
    FollowsSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    RestPasswordRequestSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    VerifyResetPasswordOTPSerializer,
)
from uia_backend.accounts.api.v1.throttles import PasswordRestThrottle
from uia_backend.accounts.models import CustomUser, Follows


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
                    "message": "You followed John Doe successfully.",
                },
            )
        ]
    )
    def post(self, request: Request, user_id: str) -> Response:
        """Follow a user by id"""
        try:
            user_to = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {
                    "info": "Failure",
                    "message": "The user to follow does not exist.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if self.request.user.id != user_to.id:
            data = {"user_from": self.request.user, "user_to": user_to}
            serializer = FollowsSerializer(data=data)

            if serializer.is_valid():
                serializer.save()

                return Response(
                    {
                        "info": "Success",
                        "message": f"You followed {user_to.get_full_name()} successfully.",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "info": "Failure",
                        "message": f"You already follow {user_to.get_full_name()}.",
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            return Response(
                {
                    "info": "Failure",
                    "message": f"You cannot unfollow {user_to.get_full_name()}. You didn't follow them.",
                },
                status=status.HTTP_40O_BAD_REQUEST,
            )


class UnFollowAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = FollowsSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["delete"]

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
                    "message": "You unfollowed John Doe successfully.",
                },
            )
        ]
    )
    def delete(self, request: Request, user_id: str) -> Response:
        """Unfollow a user by id"""
        try:
            user_to = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {
                    "info": "Failure",
                    "message": "The user to unfollow does not exist.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if self.request.user.id != user_to.id:
            follow_relationship = Follows.objects.filter(
                user_from=self.request.user, user_to=user_to
            ).first()

            if follow_relationship:
                serializer = FollowsSerializer(follow_relationship)

                if serializer.is_valid():
                    follow_relationship.delete()

                    return Response(
                        {
                            "info": "Success",
                            "message": f"You unfollowed {user_to.get_full_name()} successfully.",
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {
                            "info": "Failure",
                            "message": f"You cannot unfollow {user_to.get_full_name()}. You didn't follow them.",
                        },
                        status=status.HTTP_40O_BAD_REQUEST,
                    )
        else:
            return Response(
                {
                    "info": "Failure",
                    "message": f"You cannot unfollow {user_to.get_full_name()}. You didn't follow them.",
                },
                status=status.HTTP_40O_BAD_REQUEST,
            )


class FollowerListAPIView(generics.RetrieveAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user
        followers = user.get_followers()
        # followers_count = user.get_followers_count()
        serializer = self.get_serializer(followers, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class FollowingListAPIView(generics.RetrieveAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user
        following = user.get_following()
        # following_count = user.get_following_count()
        serializer = self.get_serializer(following, many=True)
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
