from rest_framework import serializers
from friendship.models import FriendsRelationship
from accounts.api.v1.serializers import (
    UserRegistrationSerializer
)    

from uia_backend.accounts.models import CustomUser

class FriendRequestSerializer(serializers.ModelSerializer):
    sender = UserRegistrationSerializer(read_only=True, many=True)
    # receiver = UserRegistrationSerializer(read_only=True, many=True)

    class Meta:
        model  = FriendsRelationship
        fields = ["id", "sender"]

class AcceptFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FriendsRelationship
        fields = ["id", "sender", "receiver"]

class RejectFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FriendsRelationship
        fields = ["id", "sender", "receiver"]


class BlockFriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendsRelationship
        fields = ["id", "sender", "receiver"]


    



