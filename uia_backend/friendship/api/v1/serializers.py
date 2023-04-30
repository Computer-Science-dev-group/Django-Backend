from typing import Any

from rest_framework import serializers

from uia_backend.accounts.api.v1.serializers import UserRegistrationSerializer
from uia_backend.friendship.models import FriendsRelationship
from uia_backend.libs.default_serializer import StructureSerializer


class FriendRequestSerializer(serializers.ModelSerializer):
    sender = UserRegistrationSerializer(read_only=True, many=True)
    receiver = UserRegistrationSerializer(read_only=True, many=True)

    class Meta:
        model = FriendsRelationship
        fields = ["sender", "receiver"]

    def validate(self, data: dict[str, Any]):
        sender = self.context["sender"]
        receiver = self.context["receiver"]

        if sender == receiver:
            raise serializers.ValidationError(
                "You can't send a friend request to yourself."
            )

        return data

    def to_representation(self, instance: Any) -> Any:
        data = "Friend request sent successfully."
        return StructureSerializer.to_representation(data=data)


class AcceptFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendsRelationship
        fields = ["sender", "receiver"]

    def to_representation(self, instance: Any) -> Any:
        data = "Friend request accepted successfully."
        return StructureSerializer.to_representation(data=data)


class RejectFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendsRelationship
        fields = ["sender", "receiver"]

    def to_representation(self, instance: Any) -> Any:
        data = "Friend request rejected successfully."
        return StructureSerializer.to_representation(data=data)


class BlockFriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendsRelationship
        fields = ["sender", "receiver"]

    def to_representation(self, instance: Any) -> Any:
        data = "Friend blocked successfully."
        return StructureSerializer.to_representation(data=data)
