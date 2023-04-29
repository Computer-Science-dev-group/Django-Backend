from typing import Any

from rest_framework import serializers

from uia_backend.accounts.api.v1.serializers import UserRegistrationSerializer
from uia_backend.friendship.models import FriendsRelationship
from uia_backend.libs.default_serializer import StructureSerializer


class FriendRequestSerializer(serializers.ModelSerializer):
    sender = UserRegistrationSerializer(read_only=True, many=True)
    # receiver = UserRegistrationSerializer(read_only=True, many=True)

    class Meta:
        model = FriendsRelationship
        fields = ["sender", "receiver"]

    def validate(self, data):
        sender = data.get("sender")
        receiver = data.get("receiver")

        if sender == receiver:
            raise serializers.ValidationError(
                "You can't send a friend request to yourself."
            )

        return data

    def create(self, validated_data):
        sender = validated_data.get("sender")
        receiver = validated_data.get("receiver")
        validated_data["invite_status"] = "pending"

        if FriendsRelationship.objects.filter(
            sender=sender, receiver=receiver
        ).exists():
            raise serializers.ValidationError(
                "You have already sent a friend request to this user."
            )

        if FriendsRelationship.objects.filter(
            sender=receiver, receiver=sender
        ).exists():
            raise serializers.ValidationError(
                "You have already received a friend request from this user."
            )

        return FriendsRelationship.objects.create(**validated_data)

    def to_representation(self, instance: Any) -> Any:
        data = "Friend request sent successfully."
        return StructureSerializer.to_representation(data=data)


class AcceptFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendsRelationship
        fields = ["sender", "receiver"]

    # change the invite status to accepted and is_friend to true
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if instance.invite_status == "accepted":
            instance.is_friend = True
            instance.save()
        return instance

    def to_representation(self, instance: Any) -> Any:
        data = "Friend request accepted successfully."
        return StructureSerializer.to_representation(data=data)


class RejectFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendsRelationship
        fields = ["sender", "receiver", "invite_status"]

    def validate(self, data):
        invite_status = data.get("invite_status")
        if invite_status == "rejected":
            raise serializers.ValidationError(
                "You have already rejected this friend request."
            )
        return data

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        validated_data["invite_status"] = "rejected"

        if instance.invite_status == "rejected":
            instance.is_friend = False
            instance.save()
        return instance

    def to_representation(self, instance: Any) -> Any:
        data = "Friend request rejected successfully."
        return StructureSerializer.to_representation(data=data)


class BlockFriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendsRelationship
        fields = ["sender", "receiver"]

    def validate(self, data):
        sender = data.get("sender")
        receiver = data.get("receiver")

        if sender == receiver:
            raise serializers.ValidationError("You can't block yourself.")

        return data

    def to_representation(self, instance: Any) -> Any:
        data = "Friend blocked successfully."
        return StructureSerializer.to_representation(data=data)
