from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from uia_backend.accounts.api.v1.views import (
    ChangePasswordAPIView,
    EmailVerificationAPIView,
    FriendShipInvitationDetailAPIView,
    FriendShipInvitationListAPIView,
    LoginAPIView,
    ResetPasswordAPIView,
    ResetPasswordRequestAPIView,
    UserFeedAPIView,
    UserFriendShipsDetailAPIView,
    UserFriendShipsListAPIView,
    UserProfileAPIView,
    UserProfileDetailAPIView,
    UserProfileListView,
    UserRegistrationAPIView,
    VerifyResetPasswordAPIView,
)

urlpatterns = [
    path("signup/", UserRegistrationAPIView.as_view(), name="user_registration"),
    path("signin/", LoginAPIView.as_view(), name="user_signin"),
    path("token-refesh/", TokenRefreshView.as_view(), name="token_refresh"),
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
    path("list/", UserProfileListView.as_view(), name="accounts_list"),
    path(
        "list/<uuid:user_id>/",
        UserProfileDetailAPIView.as_view(),
        name="accounts_detail",
    ),
    path(
        "me/friendships/", UserFriendShipsListAPIView.as_view(), name="user_friendships"
    ),
    path(
        "me/friendships/<uuid:pk>/",
        UserFriendShipsDetailAPIView.as_view(),
        name="user_friendship_details",
    ),
    path(
        "me/friendships/invitations/",
        FriendShipInvitationListAPIView.as_view(),
        name="friendship_invitation",
    ),
    path(
        "me/friendships/invitations/<uuid:pk>/",
        FriendShipInvitationDetailAPIView.as_view(),
        name="friendship_invitation_detail",
    ),
    path("me/feed/", UserFeedAPIView.as_view(), name="user_feed"),
]
