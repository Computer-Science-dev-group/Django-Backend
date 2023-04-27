from django.test import TestCase
from rest_framework.exceptions import ValidationError
from uia_backend.accounts.models import CustomUser
from uia_backend.friendship.models import FriendsRelationship
from uia_backend.friendship.api.v1.serializers import FriendRequestSerializer
from uia_backend.friendship.api.v1.serializers import(
    FriendRequestSerializer,
    AcceptFriendRequestSerializer,
    RejectFriendRequestSerializer,
    BlockFriendSerializer,
)




class FriendRequestSerializerTest(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            email="user1@example.com", password="password"
        )
        self.user2 = CustomUser.objects.create_user(
        email="user2@example.com", password="password"
        )
    
    def test_create(self):
        data = {
            "sender": str(self.user1.id),
            "receiver": str(self.user2.id),
            "is_friend": False,
            "invite_status": "pending",
            "is_blocked": False,
        }
        serializer = FriendRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        friendship = serializer.save()
        self.assertIsInstance(friendship, FriendsRelationship)
        self.assertEqual(friendship.sender, self.user1)
        self.assertEqual(friendship.receiver, self.user2)
        self.assertFalse(friendship.is_friend)
        self.assertEqual(friendship.invite_status, "pending")
        self.assertFalse(friendship.is_blocked)

    def test_validate_receiver_is_not_sender(self):
        data = {
            "sender": str(self.user1.id),
            "receiver": str(self.user1.id),
            "is_friend": False,
            "invite_status": "pending",
            "is_blocked": False,
        }
        serializer = FriendRequestSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_validate_friendship_does_not_exist(self):
        FriendsRelationship.objects.create(sender=self.user1, receiver=self.user2)
        data = {
            "sender": str(self.user1.id),
            "receiver": str(self.user2.id),
            "is_friend": False,
            "invite_status": "pending",
            "is_blocked": False,
        }
        serializer = FriendRequestSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_send_self_friend_request(self):
        data = {
            "sender": str(self.user1.id),
            "receiver": str(self.user1.id),
            "is_friend": False,
            "invite_status": "pending",
            "is_blocked": False,
        }
        serializer = FriendRequestSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
        

    def test_reject_friend_request(self):
        friendship = FriendsRelationship.objects.create(sender=self.user1, receiver=self.user2)
        data = {
            "id": str(friendship.id),
            "sender": str(self.user1.id),
            "receiver": str(self.user2.id),
            "is_friend": False,
            "invite_status": "rejected",
            "is_blocked": False,
        }
        serializer = RejectFriendRequestSerializer(friendship, data=data)
        self.assertTrue(serializer.is_valid())
        friendship = serializer.save()
        self.assertEqual(friendship.invite_status, "rejected")
