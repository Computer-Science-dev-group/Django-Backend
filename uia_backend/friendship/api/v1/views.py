from typing import Any
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import response

from uia_backend.accounts.api.v1.serializers import UserRegistrationSerializer
from uia_backend.accounts.models import CustomUser
from uia_backend.friendship.api.v1.serializers import (
    AcceptFriendRequestSerializer,
    BlockFriendSerializer,
    FriendRequestSerializer,
    RejectFriendRequestSerializer,
)
from uia_backend.friendship.models import FriendsRelationship


class SendFriendRequestView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendRequestSerializer
    queryset = FriendsRelationship.objects.all() 

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = FriendRequestSerializer(data=request.data, context={
            "receiver_id": kwargs["receiver_id"],
            "sender_id": request.user.id
        })
        
        serializer.is_valid(raise_exception=True)

        sender = CustomUser.objects.get(id = serializer.validated_data["receiver_id"])
        receiver = CustomUser.objects.get(id = serializer.validated_data["sender_id"])
        
        if FriendsRelationship.objects.filter(sender=sender, receiver=receiver).exists():
            return Response({
                "info": "You have sent friend request alread"
            })
        
        else:
            friendship = FriendsRelationship.objects.create(
            sender=sender, 
            receiver=receiver, 
            invite_status="accepted", 
            is_friend=True
            )
       
        return Response({"status": "success",
                         "info": "friend request sent"
                         }, status=status.HTTP_200_OK) 

        

class AcceptFriendRequestView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AcceptFriendRequestSerializer
    queryset = FriendsRelationship.objects.all()
    lookup_field = "pk"

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.invite_status = "accepted"
        instance.is_friend = True
        instance.save()

        return Response(
            data={
                "info": "success",
                "detail": f"You have accepted {instance.sender} friend request",
            },
            status=status.HTTP_200_OK,
        )


class RejectFriendRequestView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RejectFriendRequestSerializer
    queryset = FriendsRelationship.objects.all()
    lookup_field = "pk"

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.invite_status = "rejected"
        instance.delete()
        return Response(
            data={
                "info": "success",
                "details": f"Friend request from {instance.sender.first_name} has been rejected ",
            },
            status=status.HTTP_200_OK,
        )


class BlockFriendView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = FriendsRelationship.objects.all()
    serializer_class = BlockFriendSerializer
    lookup_field = "pk"

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_friend = False
        instance.invite_status = "rejected"
        instance.is_blocked = True
        instance.save()

        return Response(
            data={
                "info": "success",
                "details": f"{instance.sender.first_name} has been blocked Succefully",
            },
            status=status.HTTP_200_OK,
        )

