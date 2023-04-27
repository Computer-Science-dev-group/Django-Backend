from rest_framework.test import APITestCase
from tests.friendship.test_models import FriendShipModelFactory



class FriendShipv1Tests(APITestCase):
    def setUp(self) -> None:
        sender
        self.user = FriendShipModelFactory.create()
        