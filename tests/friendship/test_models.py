from django.test import TestCase
from factory.django import DjangoModelFactory
from uia_backend.friendship.models import FriendsRelationship
from uia_backend.accounts.models import CustomUser
import factory
import pytest




class FriendShipModelFactory(DjangoModelFactory):
    sender = factory.SubFactory(CustomUser)
    receiver = factory.SubFactory(CustomUser)
    is_friend = False
    invite_status = "pending"
    is_blocked = False

    class Meta:
        model = FriendsRelationship
        
    
@pytest.mark.django_db
class FriendTests(TestCase):

    def test_unicode(self):
        user1=CustomUser.objects.create_user(email='user1@example.com',password='pass')
        user2=CustomUser.objects.create_user(email='user2@examplde.com',password='pass')
        friend = FriendShipModelFactory.create(sender=user1,receiver=user2)
        self.assertEqual(str(friend), f"Friend Request from {user1} to {user2}")


    def test_friend_request(self):
        user1=CustomUser.objects.create_user(email='user1@example.com',password='pass')
        user2=CustomUser.objects.create_user(email='user2@examplde.com',password='pass')
        friend = FriendShipModelFactory.create(sender=user1,receiver=user2)
        self.assertEqual(friend.invite_status, "pending")
        self.assertEqual(friend.is_friend, False)
        self.assertEqual(friend.is_blocked, False)

    def test_friend_request_accept(self):
        user1=CustomUser.objects.create_user(email='user1@example.com',password='pass')
        user2=CustomUser.objects.create_user(email='user2@examplde.com',password='pass')
        friend = FriendShipModelFactory.create(sender=user1,receiver=user2)
        friend.invite_status = "accepted"
        friend.is_friend = True
        self.assertEqual(friend.invite_status, "accepted")
        self.assertEqual(friend.is_friend, True)
        self.assertEqual(friend.is_blocked, False)

    def test_friend_request_reject(self):
        user1=CustomUser.objects.create_user(email='user1@example.com',password='pass')
        user2=CustomUser.objects.create_user(email='user2@examplde.com',password='pass')
        friend = FriendShipModelFactory.create(sender=user1,receiver=user2)
        friend.invite_status = 'rejected'
        friend.is_friend = False
        self.assertEqual(friend.invite_status,'rejected')
        self.assertEqual(friend.is_friend,False)
        self.assertEqual(friend.is_blocked,False)

    def test_friend_request_without_sender(self):
        user = CustomUser.objects.create_user(email='user@mail.com',password='pass')
        with self.assertRaises(ValueError):
            FriendsRelationship.objects.create(sender=None, receiver=user)

    def test_friend_request_without_receiver(self): 
        user = CustomUser.objects.create_user(email='user@mail.com',password='pass')
        with self.assertRaises(ValueError):
            FriendsRelationship.objects.create(sender=user, receiver=None)

    def test_friend_is_blocked(self):
        user1=CustomUser.objects.create_user(email='user1@example.com',password='pass')
        user2=CustomUser.objects.create_user(email='user2@mail.com',password='pass')
        friend = FriendShipModelFactory.create(sender=user1,receiver=user2)
        friend.is_blocked = True
        self.assertEqual(friend.is_blocked,True)

    def test_friend_is_not_blocked(self):
        user1=CustomUser.objects.create_user(email='user1@example.com',password='pass')
        user2=CustomUser.objects.create_user(email='user2@mail.com',password='pass')
        friend = FriendShipModelFactory.create(sender=user1,receiver=user2)
        friend.is_blocked = False
        self.assertEqual(friend.is_blocked,False)


