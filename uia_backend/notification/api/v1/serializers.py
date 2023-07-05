from typing import Any

from rest_framework import serializers

from uia_backend.accounts.api.v1.serializers import UserProfileSerializer
from uia_backend.accounts.models import CustomUser
from uia_backend.notification.models import NotificationModel


class GenericNotificationRelatedField(serializers.RelatedField):
    def to_representation(self, value: Any) -> Any:
        """Properly parse notification actor or target objects."""

        # NOTE: This needs to be updated as we progress

        if isinstance(value, CustomUser):
            serializer = UserProfileSerializer(instance=value)
            data = serializer.data
        else:
            data = None

        return data


class NotificationSerializer(serializers.ModelSerializer[NotificationModel]):
    actor = GenericNotificationRelatedField(read_only=True)
    target = GenericNotificationRelatedField(read_only=True)
    recipient = UserProfileSerializer(read_only=True)
    data = serializers.JSONField(read_only=True)

    class Meta:
        model = NotificationModel
        fields = [
            "id",
            "recipient",
            "type",
            "verb",
            "timestamp",
            "actor",
            "target",
            "unread",
            "data",
        ]
        read_only_fields = [
            "id",
            "recipient",
            "type",
            "verb",
            "timestamp",
            "actor",
            "target",
            "data",
        ]

    def create(self, validated_data: Any) -> NotificationModel:
        """Overidden field"""
