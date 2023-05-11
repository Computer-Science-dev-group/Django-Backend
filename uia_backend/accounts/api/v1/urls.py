from django.urls import path

from uia_backend.accounts.api.v1.views import (
    ChangePasswordAPIView,
    EmailVerificationAPIView,
    FriendShipInvitationDetailAPIView,
    FriendShipInvitationListAPIView,
    FollowAPIView,
    FollowerListAPIView,
    FollowingListAPIView,
    LoginAPIView,
    ResetPasswordAPIView,
    ResetPasswordRequestAPIView,
    UserFriendShipsDetailAPIView,
    UserFriendShipsListAPIView,
    UserProfileAPIView,
    UserProfileListView,
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
    path("list/", UserProfileListView.as_view(), name="accounts_list"),
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
    ),   name="friendship_invitation_detail",
    path(
        "me/follow/<uuid:user_id>", FollowAPIView.as_view(), name="user_follow_unfollow"
    ),
    path(
        "me/followers", FollowerListAPIView.as_view(), name="user_followers_list"
    ),
    path(
        "me/following", FollowingListAPIView.as_view(), name="user_following_list"
    ),
]
