from django.urls import path

from uia_backend.accounts.api.v1.views import (
    EmailVerificationAPIView,
    UserRegistrationAPIView,
    UserLoginView
)

urlpatterns = [
    path("", UserRegistrationAPIView.as_view(), name="user_registration"),
    path(
        "email-verification/<str:signature>/",
        EmailVerificationAPIView.as_view(),
        name="email_verification",
    ),
    #create a login path here
    path(
        "login/",
        UserLoginView.as_view(), 
        name="user_login"    
    ),
]
