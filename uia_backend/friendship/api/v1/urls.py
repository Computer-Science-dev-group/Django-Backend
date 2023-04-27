from django.urls import path
from friendship.api.v1.views import(
    SendFriendRequestView,
    AcceptFriendRequestView,
    RejectFriendRequestView,
    BlockFriendView,
)

urlpatterns = [
        path("send-friend-request/<str:sender_id>/<str:receiver_id>/", SendFriendRequestView.as_view(), name="send-friend-request"),
        path("accept-friend-request/<int:pk>/", AcceptFriendRequestView.as_view(), name="accept-friend-request"),
        path("reject-friend-request/<int:pk>/", RejectFriendRequestView.as_view(), name="reject-friend-request"),
        path("block-friend/<int:pk>", BlockFriendView.as_view(), name="block-friend"), 
        
    ]
