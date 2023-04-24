from django.urls import path

from uia_backend.accounts.api.v1.views import (
    ChangePasswordAPIView,
    EmailVerificationAPIView,
    UserProfileAPIView,
    LoginAPIView,
    UserRegistrationAPIView,
)

urlpatterns = [
    path("signup", UserRegistrationAPIView.as_view(), name="user_registration"),
    path("signin", LoginAPIView.as_view(), name="user_signin"),
    path(
        "email-verification/<str:signature>/",
        EmailVerificationAPIView.as_view(),
        name="email_verification",
    ),
    # AUTHENTICATED USER SPECIFIC VIEWS
    path("me/profile/", UserProfileAPIView.as_view(), name="user_profile"),
    path(
        "me/change-password/", ChangePasswordAPIView.as_view(), name="change_password"
    ),
]
