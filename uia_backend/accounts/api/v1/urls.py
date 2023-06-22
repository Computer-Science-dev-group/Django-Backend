from django.urls import path

from uia_backend.accounts.api.v1.views import (
    ChangePasswordAPIView,
    EmailVerificationAPIView,
    FollowAPIView,
    FollowerListAPIView,
    FollowingListAPIView,
    LoginAPIView,
    UserProfileAPIView,
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
    path(
        "me/follow/<uuid:user_id>/", FollowAPIView.as_view(), name="user_follow_or_unfollow"
    ),
    path(
        "me/followers/", FollowerListAPIView.as_view(), name="user_followers_list"
    ),
    path(
        "me/following/", FollowingListAPIView.as_view(), name="user_following_list"
    ),
]
