from django.urls import path

from uia_backend.friendship.api.v1.views import (
    AcceptFriendRequestView,
    BlockFriendView,
    RejectFriendRequestView,
    SendFriendRequestView,
)

urlpatterns = [
    path(
        "send-friend-request/<uuid:receiver_id>",
        SendFriendRequestView.as_view(),
        name="send-friend-request",
    ),
    path(
        "accept-friend-request/<int:pk>/",
        AcceptFriendRequestView.as_view(),
        name="accept-friend-request",
    ),
    path(
        "reject-friend-request/<int:pk>/",
        RejectFriendRequestView.as_view(),
        name="reject-friend-request",
    ),
    path("block-friend/<int:pk>", BlockFriendView.as_view(), name="block-friend"),
]
