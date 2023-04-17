from typing import Any

from django.db import transaction
from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response

from uia_backend.accounts.api.v1.serializers import (
    EmailVerificationSerializer,
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
