from rest_framework import serializers
from uia_backend.friendship.models import FriendsRelationship
from uia_backend.accounts.api.v1.serializers import (
    UserRegistrationSerializer
)    

from uia_backend.accounts.models import CustomUser

class FriendRequestSerializer(serializers.ModelSerializer):
    sender = UserRegistrationSerializer(read_only=True, many=True)
    
    class Meta:
        model  = FriendsRelationship
        fields = ["sender"]

class AcceptFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FriendsRelationship
        fields = []

class RejectFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FriendsRelationship
        fields = []


class BlockFriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendsRelationship
        fields = []


    



