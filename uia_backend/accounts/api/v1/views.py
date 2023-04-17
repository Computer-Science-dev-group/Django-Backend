from typing import Any

from django.core.serializers.json import Serializer
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response

from uia_backend.accounts.api.v1.serializers import (
    EmailVerificationSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)


class UserRegistrationAPIView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @transaction.atomic()
    def post(self, request: Request, *args: Any, **kwargs: dict[str, Any]) -> Response:
        return super().post(request, *args, **kwargs)


# NOTE: For now lets use a API request for this later we can build a nice looking template
# NOTE: We also have to figure out a way to handle verification for web
# (we may want to redirect to the web app or something)
class EmailVerificationAPIView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.AllowAny]

    @transaction.atomic()
    def get(self, request: Request, signature: str) -> Response:
        serializer = self.get_serializer(data={"signature": signature})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            data={
                "info": "Success",
                "message": "Your account has been successfully verified.",
            }
        )

class UserProfileAPIView(generics.GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer(self, *args, **kwargs):
        """Override default serializer behavior to only allow write-only fields to be updated"""

        serializer = super().get_serializer(*args, **kwargs)

        read_only_fields = ["year_of_graduation", "department", "faculty_or_college"]

        for field in read_only_fields:
            if field in serializer.fields:
                serializer.fields[field].read_only = True
        
        write_only_fields = [
            "first_name", 
            "last_name", 
            "profile_picture", 
            "cover_photo",
            "phone_number",
            "display_name",
            "bio", 
            "gender", 
            "date_of_birth",
        ]

        for field in write_only_fields:
            if field in serializer.fields:
                serializer.fields[field].read_only = False
        return serializer
    
    @transaction.atomic()
    def put(self, request, *args, **kwargs) -> Response:
        """Initial User Profile update after registration"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                data={
                    "info": "Success",
                    "message": "Your profile has been successfully updated",
                }
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic()
    def patch(self, request, *args, **kwargs) -> Response:
        """Subsequent updates to the user profile through the patch method"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                data={
                    "info": "Success",
                    "message": "Your profile has been successfully updated",
                }
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

