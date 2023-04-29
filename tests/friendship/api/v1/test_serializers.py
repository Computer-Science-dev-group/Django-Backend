from tests.accounts.test_models import UserModelFactory

# from tests.friendship.test_models import FriendShipModelFactory
from uia_backend.friendship.api.v1.serializers import (
    AcceptFriendRequestSerializer,
    FriendRequestSerializer,
)
from uia_backend.libs.testutils import CustomSerializerTests

# class FriendRequestSerializerTest(TestCase):
#     def setUp(self):
#         self.user1 = CustomUser.objects.create_user(
#             email="user1@example.com", password="password"
#         )
#         self.user2 = CustomUser.objects.create_user(
#         email="user2@example.com", password="password"
#         )

#     def test_create(self):
#         data = {
#             "sender": str(self.user1.id),
#             "receiver": str(self.user2.id),
#             "is_friend": False,
#             "invite_status": "pending",
#             "is_blocked": False,
#         }
#         serializer = FriendRequestSerializer(data=data)
#         self.assertTrue(serializer.is_valid())
#         friendship = serializer.save()
#         self.assertIsInstance(friendship, FriendsRelationship)
#         self.assertEqual(friendship.sender, self.user1)
#         self.assertEqual(friendship.receiver, self.user2)
#         self.assertFalse(friendship.is_friend)
#         self.assertEqual(friendship.invite_status, "pending")
#         self.assertFalse(friendship.is_blocked)

#     def test_validate_receiver_is_not_sender(self):
#         data = {
#             "sender": str(self.user1.id),
#             "receiver": str(self.user1.id),
#             "is_friend": False,
#             "invite_status": "pending",
#             "is_blocked": False,
#         }
#         serializer = FriendRequestSerializer(data=data)
#         with self.assertRaises(ValidationError):
#             serializer.is_valid(raise_exception=True)

#     def test_validate_friendship_does_not_exist(self):
#         FriendsRelationship.objects.create(sender=self.user1, receiver=self.user2)
#         data = {
#             "sender": str(self.user1.id),
#             "receiver": str(self.user2.id),
#             "is_friend": False,
#             "invite_status": "pending",
#             "is_blocked": False,
#         }
#         serializer = FriendRequestSerializer(data=data)
#         with self.assertRaises(ValidationError):
#             serializer.is_valid(raise_exception=True)

#     def test_send_self_friend_request(self):
#         data = {
#             "sender": str(self.user1.id),
#             "receiver": str(self.user1.id),
#             "is_friend": False,
#             "invite_status": "pending",
#             "is_blocked": False,
#         }
#         serializer = FriendRequestSerializer(data=data)
#         with self.assertRaises(ValidationError):
#             serializer.is_valid(raise_exception=True)


#     def test_reject_friend_request(self):
#         friendship = FriendsRelationship.objects.create(sender=self.user1, receiver=self.user2)
#         data = {
#             "id": str(friendship.id),
#             "sender": str(self.user1.id),
#             "receiver": str(self.user2.id),
#             "is_friend": False,
#             "invite_status": "rejected",
#             "is_blocked": False,
#         }
#         serializer = RejectFriendRequestSerializer(friendship, data=data)
#         self.assertTrue(serializer.is_valid())
#         friendship = serializer.save()
#         self.assertEqual(friendship.invite_status, "rejected")

#     def test_send_friend_request(self):
#         friendship = FriendsRelationship.objects.create(sender=self.user1, receiver=self.user2)
#         data = {
#             "id": str(friendship.id),
#             "sender": str(self.user1.id),
#             "receiver": str(self.user2.id),
#             "is_friend": True,
#             "invite_status": "pending",
#             "is_blocked": False,
#         }
#         serializer = AcceptFriendRequestSerializer(friendship, data=data)
#         self.assertTrue(serializer.is_valid())
#         friendship = serializer.save()
#         self.assertEqual(friendship.invite_status, "pending")


#     def test_block_friend(self):
#         friendship = FriendsRelationship.objects.create(sender=self.user1, receiver=self.user2)
#         data = {
#             "id": str(friendship.id),
#             "sender": str(self.user1.id),
#             "receiver": str(self.user2.id),
#             "is_friend": False,
#             "invite_status": "rejected",
#             "is_blocked": True,
#         }
#         serializer = BlockFriendSerializer(friendship, data=data)
#         self.assertTrue(serializer.is_valid())
#         friendship = serializer.save()
#         self.assertEqual(friendship.is_blocked, True)


class AcceptFriendRequestSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = AcceptFriendRequestSerializer

    REQUIRED_FIELDS = ["sender", "receiver"]

    NON_REQUIRED_FIELDS = []

    def setUp(self):
        user1 = UserModelFactory.create(email="abdullahi@mail.com", is_active=True)
        user2 = UserModelFactory.create(email="abdullahi@mail.com", is_active=True)
        # friendship = FriendShipModelFactory.create(
        #     sender=user1, receiver=user2, is_friend=False, invite_status="pending"
        # )

        self.VALID_DATA = [
            {
                "data": {
                    "sender": user1.id,
                    "receiver": user2.id,
                    "is_friend": True,
                    "invite_status": "accepted",
                },
                "lable": "Test valid data",
                "context": None,
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "sender": "kfsajkcinwdjfj",
                    "receiver": user2.id,
                    "is_friend": False,
                    "invite_status": "accepted",
                },
                "lable": "Test invalid data users not friends",
                "context": None,
            },
        ]


class FriendRequestSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = FriendRequestSerializer

    REQUIRED_FIELDS = ["sender"]

    NON_REQUIRED_FIELDS = []

    def setUp(self):
        user1 = UserModelFactory.create(email="abdullahi@mail.com", is_active=True)
        user2 = UserModelFactory.create(email="user@example.com", is_active=True)

        self.VALID_DATA = [
            {
                "data": {"sender": user1.id, "receiver": user2.id},
                "lable": "Test valid data",
                "context": None,
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {"sender": "0909scjsfnwjenfcjwef", "receiver": user2.id},
                "lable": "Test invalid data wrong sender id",
                "context": None,
            },
            {
                "data": {"sender": user1.id, "receiver": "reofdk-wvjpfpdks-3jndn"},
                "lable": "Test invalid data wrong reciever id",
                "context": None,
            },
            {
                "data": {"sender": user1.id, "receiver": user2.id},
                "lable": "Test innvalid data same sender id",
                "context": None,
            },
        ]
