import uuid
from unittest.mock import MagicMock

from tests.accounts.test_models import UserModelFactory
from uia_backend.cluster.api.v1.serializers import (
    ClusterInvitationSerializer,
    ClusterSerializer,
)
from uia_backend.libs.testutils import CustomSerializerTests, get_test_image_file


class ClusterSerializerTests(CustomSerializerTests):
    __test__ = True
    serializer_class = ClusterSerializer

    REQUIRED_FIELDS = ["title"]
    NON_REQUIRED_FIELDS = ["id", "created_by", "is_default", "description", "icon"]

    VALID_DATA = [
        {
            "data": {"title": "string", "description": "string", "icon": None},
            "label": "Test valid data icon is Null",
            "context": None,
        },
        {
            "data": {"title": "string", "description": "", "icon": None},
            "label": "Test valid data icon is Null and description is empty",
            "context": None,
        },
        {
            "data": {
                "title": "string",
                "description": "AYayayayaya",
                "icon": get_test_image_file(),
            },
            "label": "Test valid data icon has file",
            "context": None,
        },
    ]

    INVALID_DATA = [
        {
            "data": {
                "title": "",
                "description": "Naaana",
                "icon": get_test_image_file(),
            },
            "label": "Test Invalid data empty title.",
            "context": None,
            "error": {"title": ["This field may not be blank."]},
        },
    ]


class ClusterInvitationSerializerTests(CustomSerializerTests):
    __test__ = True
    serializer_class = ClusterInvitationSerializer

    REQUIRED_FIELDS = ["user", "duration"]
    NON_REQUIRED_FIELDS = ["id", "created_by", "cluster", "status"]

    def setUp(self) -> None:
        authenticated_user = UserModelFactory.create(
            is_active=True, email="email1@example.com"
        )
        invited_user = UserModelFactory.create(
            is_active=True, email="email34@example.com"
        )

        request = MagicMock()
        request.user = authenticated_user

        self.VALID_DATA = [
            {
                "data": {
                    "status": 0,
                    "duration": 10,
                    "user": str(invited_user.id),
                },
                "label": "Test valid data",
                "context": {"request": request},
            },
            {
                "data": {"duration": 1, "user": str(invited_user.id)},
                "label": "Test valid data",
                "context": {"request": request},
            },
        ]

        some_uuid = str(uuid.uuid4())
        self.INVALID_DATA = [
            {
                "data": {
                    "status": 5,
                    "duration": 10,
                    "user": str(invited_user.id),
                },
                "label": "Test invalid status",
                "context": {"request": request},
                "error": {"status": ['"5" is not a valid choice.']},
            },
            {
                "data": {
                    "status": 0,
                    "duration": 0,
                    "user": str(invited_user.id),
                },
                "label": "Test invalid duration",
                "context": {"request": request},
                "error": {
                    "duration": ["Ensure this value is greater than or equal to 1."]
                },
            },
            {
                "data": {
                    "status": 0,
                    "duration": 10,
                    "user": some_uuid,
                },
                "label": "Test invalid user",
                "context": {"request": request},
                "error": {
                    "user": [f'Invalid pk "{some_uuid}" - object does not exist.']
                },
            },
            {
                "data": {
                    "status": 0,
                    "duration": 10,
                    "user": str(authenticated_user.id),
                },
                "label": "Test invalid user. Can not send invitation to yourself.",
                "context": {"request": request},
                "error": {
                    "user": ["Invalid user. Can not send inivitation to this user."]
                },
            },
        ]


class ClusterMembershipSerializer(CustomSerializerTests):
    REQUIRED_FIELDS = []
    NON_REQUIRED_FIELDS = ["id", "user"]

    VALID_DATA = []
    INVALID_DATA = []
