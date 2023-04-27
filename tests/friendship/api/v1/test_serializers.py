from uia_backend.libs.testutils import CustomSerializerTests
from uia_backend.friendship.api.v1.serializers import(
    FriendRequestSerializer,
    AcceptFriendRequestSerializer,
    RejectFriendRequestSerializer,
    BlockFriendSerializer,
)

def FriendRequestSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = FriendRequestSerializer

    REQUIRED_FIELDS = [
        "id",
        "sender",
        "email",
        "password",
        "faculty",
        "department",
        "year_of_graduation",
    ]