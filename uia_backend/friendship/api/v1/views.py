from rest_framework import generics, permissions, status
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

    def create(self, request, receiver_id):
        receiver_id = receiver_id
        sender_id = request.user.id

        context = {"sender": sender_id, "receiver": receiver_id}

        serializer = FriendRequestSerializer(data=request.data, context=context)
        receiver = CustomUser.objects.get(id=receiver_id)

        serializer.is_valid(raise_exception=True)
        serializer.save(sender=request.user, receiver=receiver)

        return Response(
            {
                "status": "success",
                "details": f"Your friend request to {receiver.first_name} {receiver.last_name} has been sent",
            },
            status=status.HTTP_201_CREATED,
        )


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
