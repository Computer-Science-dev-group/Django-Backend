from typing import Any

from django.db import transaction
from rest_framework import generics, permissions,views,status
from rest_framework.request import Request
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from uia_backend.accounts.models import CustomUser
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response

from uia_backend.accounts.api.v1.serializers import (
    EmailVerificationSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
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
class UserLoginView(APIView):
    serializer_class= UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request,*args,**kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email=request.data.get('email')
            password = request.data.get('password')
            try:
                user_profile= CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({'message': 'No active account found with the given credentials', "data":{}, "status":False, "status_code":1}, status=status.HTTP_401_UNAUTHORIZED)
            
            validate = user_profile.check_password(password)
            if validate:
                access_token = AccessToken.for_user(user_profile)
                refresh_token = RefreshToken.for_user(user_profile)
                return Response(
                    {'access_token': str(access_token),
                    'refresh_token': str(refresh_token),
                    "message": "Login Successful",
                    "status":True,
                    }
                ) 
            return Response({"message":"email or password not correct", "data":{}, "status":False, "status_code":1}, status=status.HTTP_401_UNAUTHORIZED)
            
                
        return Response({"message":serializer.errors, "data":{}, "status":False, "status_code":1}, status=status.HTTP_400_BAD_REQUEST)

