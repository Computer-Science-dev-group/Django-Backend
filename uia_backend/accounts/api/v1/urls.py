from django.urls import path

from uia_backend.accounts.api.v1.views import (
    EmailVerificationAPIView,
    ForgotPasswordAPIView,
    UserRegistrationAPIView,
    VerifyOTPView,
)

urlpatterns = [
    path("", UserRegistrationAPIView.as_view(), name="user_registration"),
    path(
        "email-verification/<str:signature>/",
        EmailVerificationAPIView.as_view(),
        name="email_verification",
    ),
    path(
        "forget-password/",
        ForgotPasswordAPIView.as_view(),
        name="forget_password",
    ),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
]
