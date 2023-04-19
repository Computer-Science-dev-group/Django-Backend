from django.urls import path

from uia_backend.accounts.api.v1.views import (
    EmailVerificationAPIView,
    UserRegistrationAPIView,
)

urlpatterns = [
    path("", UserRegistrationAPIView.as_view(), name="user_registration"),
    path(
        "email-verification/<str:signature>/",
        EmailVerificationAPIView.as_view(),
        name="email_verification",
    ),
]