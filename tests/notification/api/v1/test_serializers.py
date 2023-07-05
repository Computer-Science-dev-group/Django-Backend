from uia_backend.libs.testutils import CustomSerializerTests
from uia_backend.notification.api.v1.serializers import NotificationSerializer


class NotificationSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = NotificationSerializer

    REQUIRED_FIELDS = []

    NON_REQUIRED_FIELDS = [
        "id",
        "recipient",
        "type",
        "verb",
        "timestamp",
        "actor",
        "target",
        "unread",
        "data",
    ]

    VALID_DATA = [
        {
            "data": {"unread": False},
            "lable": "Test valid data",
            "context": None,
        }
    ]

    INVALID_DATA = []
