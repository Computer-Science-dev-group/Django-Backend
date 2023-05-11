from django.urls import path

from uia_backend.accounts.api.v1.views import (
    ChangePasswordAPIView,
    EmailVerificationAPIView,
    LoginAPIView,
    ResetPasswordAPIView,
    ResetPasswordRequestAPIView,
    UserProfileAPIView,
    UserRegistrationAPIView,
    VerifyResetPasswordAPIView,
)

urlpatterns = [
    path("signup/", UserRegistrationAPIView.as_view(), name="user_registration"),
    path("signin/", LoginAPIView.as_view(), name="user_signin"),
    path(
        "email-verification/<str:signature>/",
        EmailVerificationAPIView.as_view(),
        name="email_verification",
    ),
    path(
        "reset-password/request-otp/",
        ResetPasswordRequestAPIView.as_view(),
        name="request_password_reset_otp",
    ),
    path(
        "reset-password/verify-otp/",
        VerifyResetPasswordAPIView.as_view(),
        name="verify_password_reset_otp",
    ),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="reset_password"),
    # AUTHENTICATED USER SPECIFIC VIEWS
    path("me/profile/", UserProfileAPIView.as_view(), name="user_profile"),
    path(
        "me/change-password/", ChangePasswordAPIView.as_view(), name="change_password"
    ),
]
