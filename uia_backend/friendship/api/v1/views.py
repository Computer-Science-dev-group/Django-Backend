from rest_framework import generics
from rest_framework.response import Response
from friendship.models import FriendsRelationship
from rest_framework import permissions, status
from uia_backend.accounts.models import (
    CustomUser
)
from accounts.api.v1.serializers import(
    UserRegistrationSerializer
)

from friendship.api.v1.serializers import(
    FriendRequestSerializer,
    AcceptFriendRequestSerializer,
    RejectFriendRequestSerializer,
    BlockFriendSerializer,
)


class SendFriendRequestView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendRequestSerializer
    queryset = FriendsRelationship.objects.all()
   
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        receiver_id = self.kwargs['receiver_id']
        sender_id = self.request.data['id']
        
        receiver = CustomUser.objects.get(id = receiver_id)
        sender = CustomUser.objects.get(id = sender_id)
       
        if FriendsRelationship.objects.filter(sender=sender,receiver = receiver).exists():
            return Response({
                "status": "error",
                "details": "Freind request has been sent already."
                } ,status=status.HTTP_400_BAD_REQUEST)
            
        else:
            serializer.is_valid(raise_exception= True)
            serializer.save(sender= sender, receiver = receiver)   
            return Response(
                {
            "status": "success",
            "details": f"Your friend request to {receiver.first_name} {receiver.last_name} has been sent"
            }, status=status.HTTP_201_CREATED)
        

       
class AcceptFriendRequestView(generics.UpdateAPIView):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AcceptFriendRequestSerializer
    queryset = FriendsRelationship.objects.all()
    lookup_field = 'pk'
   
    def put(self, request, *args , **kwargs):
        instance = self.get_object()
        instance.invite_status = "accepted"
        instance.is_friend = True
        instance.save()
        
        return Response(data={
            "info": "success",
            "detail":f"You have accepted {instance.sender} friend request"
        }, status=status.HTTP_200_OK)
    
class RejectFriendRequestView(generics.DestroyAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RejectFriendRequestSerializer
    queryset = FriendsRelationship.objects.all()
    lookup_field = 'pk'

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.invite_status = "rejected"
        instance.delete()
        return Response(data={
            "info": "success",
            "details": f"Friend request from {instance.sender.first_name} has been rejected successfully"
        }, status=status.HTTP_200_OK)
    
class BlockFriendView(generics.UpdateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = FriendsRelationship.objects.all()
    serializer_class = BlockFriendSerializer
    lookup_field = 'pk'

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_friend = False
        instance.invite_status = 'rejected'
        instance.is_blocked = True
        instance.save()

        return Response(data={
            "info": "success",
            "details": f"{instance.sender.first_name} has been blocked Succefully"
        }, status=status.HTTP_200_OK) 



        


    
    
    
