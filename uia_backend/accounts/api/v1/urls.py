from django.urls import path

from uia_backend.accounts.api.v1.views import (
    ChangePasswordAPIView,
    EmailVerificationAPIView,
    UserProfileAPIView,
    UserRegistrationAPIView,
)

urlpatterns = [
    path("", UserRegistrationAPIView.as_view(), name="user_registration"),
    path(
        "email-verification/<str:signature>/",
        EmailVerificationAPIView.as_view(),
        name="email_verification",
    ),
    # AUTHENTICATED USER SPECIFIC VIEWS
    path("profile/", UserProfileAPIView.as_view(), name="user_profile"),
    path(
        "me/change-password/", ChangePasswordAPIView.as_view(), name="change_password"
    ),
]
