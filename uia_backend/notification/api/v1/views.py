from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from uia_backend.notification.api.v1.serializers import NotificationSerializer
from uia_backend.notification.models import NotificationModel


class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return self.request.user.notifications.all()


class NotificationDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return self.request.user.notifications.all()

    def get_object(self) -> NotificationModel:
        return get_object_or_404(
            NotificationModel, recipient=self.request.user, id=self.kwargs["id"]
        )


class MarkAllNotifcationsAsReadAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Mark all users notification as read"""
        self.request.user.notifications.mark_all_as_read()
        return Response(data={}, status=status.HTTP_200_OK)
