from rest_framework import serializers
from typing import Any
from uia_backend.friendship.models import FriendsRelationship
from uia_backend.accounts.api.v1.serializers import (
    UserRegistrationSerializer
)    

from uia_backend.accounts.models import CustomUser

class FriendRequestSerializer(serializers.ModelSerializer):
    sender = UserRegistrationSerializer(read_only=True, many=True)
    # receiver = UserRegistrationSerializer(read_only=True, many=True)

    class Meta:
        model  = FriendsRelationship
        fields = ["sender"]

    def validate(self, data):
        sender = data.get("sender")
        receiver = data.get("receiver")

        if sender == receiver:
            raise serializers.ValidationError("You can't send a friend request to yourself.")

        return data
    
    def create(self, validated_data):
        sender = validated_data.get("sender")
        receiver = validated_data.get("receiver")

        if FriendsRelationship.objects.filter(sender=sender, receiver=receiver).exists():
            raise serializers.ValidationError("You have already sent a friend request to this user.")

        if FriendsRelationship.objects.filter(sender=receiver, receiver=sender).exists():
            raise serializers.ValidationError("You have already received a friend request from this user.")

        return FriendsRelationship.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.is_friend = validated_data.get("is_friend", instance.is_friend)
        instance.invite_status = validated_data.get("invite_status", instance.invite_status)
        instance.is_blocked = validated_data.get("is_blocked", instance.is_blocked)
        instance.save()
        return instance

    



class AcceptFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FriendsRelationship
        fields = ["id", "sender", "receiver"]




class RejectFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FriendsRelationship
        fields = ["id", "sender", "receiver"]

    def update(self, instance, validated_data):
        instance.is_friend = validated_data.get("is_friend", instance.is_friend)
        instance.invite_status = validated_data.get("invite_status", instance.invite_status)
        instance.is_blocked = validated_data.get("is_blocked", instance.is_blocked)
        instance.save()
        return instance




class BlockFriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendsRelationship
        fields = ["id", "sender", "receiver"]


    def validate(self, data):
        sender = data.get("sender")
        receiver = data.get("receiver")

        if sender == receiver:
            raise serializers.ValidationError("You can't block yourself.")

        return data

