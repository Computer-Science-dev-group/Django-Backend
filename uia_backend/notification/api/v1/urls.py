from django.urls import path

from uia_backend.notification.api.v1.views import (
    MarkAllNotifcationsAsReadAPIView,
    NotificationDetailAPIView,
    NotificationListAPIView,
)

urlpatterns = [
    path("", NotificationListAPIView.as_view(), name="user_notifications"),
    path(
        "<uuid:id>/", NotificationDetailAPIView.as_view(), name="notification_details"
    ),
    path(
        "read-all/",
        MarkAllNotifcationsAsReadAPIView.as_view(),
        name="read_all_notification",
    ),
]
