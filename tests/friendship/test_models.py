from django.test import TestCase
from factory.django import DjangoModelFactory
from uia_backend.friendship.models import FriendsRelationship


class FriendModelFactory(DjangoModelFactory):
    sender = "abdullahi"
    receiver = "joseph"
    is_friend = False
    invite_status = "pending"
    is_blocked = False

    class Meta:
        model = FriendsRelationship
    

class FriendTests(TestCase):
    def test_unicode(self):
        friend = FriendModelFactory.create()
        self.assertEqual(str(friend), f"Friend Request from {friend.sender} to {friend.receiver}")

