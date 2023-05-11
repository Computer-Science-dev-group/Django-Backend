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
    UserProfileSerializer,
    UserRegistrationSerializer,
)

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
                    "message": {
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
                    "message": {
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


# class FollowUserAPIView(generics.GenericAPIView):
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_object(self) -> Any:
#         return self.request.user

#     @extend_schema(
#         examples=[
#             OpenApiExample(
#                 "Example",
#                 response_only=True,
#                 value={"info": "Success", "message": "You Followed User Successfully."},
#             )
#         ]
#     )
#     def post(self, request: Request, user_id) -> Response:
#         user_to_follow = CustomUser.objects.get(id=user_id)
#         current_user = self.get_object()

#         if user_to_follow == current_user:
#             return Response(
#                 {
#                     "info": "Failure", 
#                     "message": "You cannot follow yourself",
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         current_user.following.add(user_to_follow)
#         current_user.save()

#         return Response(
#             {
#                 "info": "Success", 
#                 "message": f"You Followed {user_to_follow.get_full_name()} Successfully",
#             },
#             status=status.HTTP_200_OK
#         )


# class UnfollowUserAPIView(generics.GenericAPIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get_object(self) -> Any:
#         return self.request.user

#     @extend_schema(
#         examples=[
#             OpenApiExample(
#                 "Example",
#                 response_only=True,
#                 value={"info": "Success", "message": "You Unfollowed User Successfully."},
#             )
#         ]
#     )
#     def post(self, request: Request, user_id) -> Response:
#         try:
#             user_to_unfollow = CustomUser.objects.get(id=user_id)
#             current_user = self.get_object()

#             current_user.following.remove(user_to_unfollow)
#             current_user.save()

#             return Response(
#                 {
#                     "info": "Success", 
#                     "message": f"You Unfollowed {user_to_unfollow.get_full_name()} Successfully.",
#                 },
#                 status=status.HTTP_200_OK
#             )
        
#         except CustomUser.DoesNotExist:
#             return Response(
#                 {
#                     "info": "Failure", 
#                     "message": "That user does not exist.",
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
    
class FollowAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> Any:
        return self.request.user

    def post(self, request: Request, user_id) -> Response:
        try:
            user_to = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {
                    "info": "Failure", 
                    "message": "That user does not exist.",
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if self.get_object() != user_to:
            if self.get_object().follow(user_to):
                return Response(
                    {
                         "info": "Success", 
                         "message": f"You followed {user_to.get_full_name()} Successfully",
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                         "info": "Success", 
                         "message": f"You already follow {user_to.get_full_name()}",
                    },
                    status=status.HTTP_200_OK
                )

        return Response(
            {
                    "info": "Failure", 
                    "message": f"You cannot unfollow {user_to.get_full_name()}. You didn't follow them.",
            },
            status=status.HTTP_40O_BAD_REQUEST
        )

    def delete(self, request: Request, user_id) -> Response:
        try:
            user_to = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {
                    "info": "Failure", 
                    "message": "That user does not exist.",
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if self.get_object() != user_to:
            self.get_object().unfollow(user_to)            
            return Response(
                {
                    "info": "Success", 
                    "message": f"You Unfollowed {user_to.get_full_name()} Successfully.",
                },
                status=status.HTTP_200_OK
            )
        
        return Response(
            {
                    "info": "Failure", 
                    "message": f"You cannot unfollow {user_to.get_full_name()}. You didn't follow them.",
            },
            status=status.HTTP_40O_BAD_REQUEST
        )


class FollowerListAPIView(generics.GenericAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, user_id) -> Response:
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {
                    "info": "Failure", 
                    "message": "That user does not exist.",
                },
                status=status.HTTP_404_NOT_FOUND
            )

        followers = user.get_followers()
        serializer = self.get_serializer(followers, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class FollowingListAPIView(generics.GenericAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id) -> Response:
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(status=404)

        following = user.get_following()
        serializer = CustomUserSerializer(following, many=True)
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
                value={"info": "Success", "message": "Password Changed Successfully."},
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
                    "info": "Success",
                    "message": {"auth_token": "jwt-token-asasasas"},
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
