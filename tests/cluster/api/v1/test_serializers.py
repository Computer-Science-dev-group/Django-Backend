import uuid
from unittest.mock import MagicMock

from tests.accounts.test_models import UserModelFactory
from tests.cluster.test_models import ClusterFactory, ClusterMembershipFactory
from uia_backend.cluster.api.v1.serializers import (
    ClusterEventSerializer,
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
            "lable": "Test valid data icon is Null",
            "context": None,
        },
        {
            "data": {"title": "string", "description": "", "icon": None},
            "lable": "Test valid data icon is Null and description is empty",
            "context": None,
        },
        {
            "data": {
                "title": "string",
                "description": "AYayayayaya",
                "icon": get_test_image_file(),
            },
            "lable": "Test valid data icon has file",
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
            "lable": "Test Invalid data empty title.",
            "context": None,
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
                "lable": "Test valid data",
                "context": {"request": request},
            },
            {
                "data": {"duration": 1, "user": str(invited_user.id)},
                "lable": "Test valid data",
                "context": {"request": request},
            },
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "status": 5,
                    "duration": 10,
                    "user": str(invited_user.id),
                },
                "lable": "Test invalid status",
                "context": {"request": request},
            },
            {
                "data": {
                    "status": 0,
                    "duration": 0,
                    "user": str(invited_user.id),
                },
                "lable": "Test invalid duration",
                "context": {"request": request},
            },
            {
                "data": {
                    "status": 0,
                    "duration": 10,
                    "user": str(uuid.uuid4()),
                },
                "lable": "Test invalid user",
                "context": {"request": request},
            },
            {
                "data": {
                    "status": 0,
                    "duration": 10,
                    "user": str(authenticated_user.id),
                },
                "lable": "Test invalid user. Can not send invitation to yourself.",
                "context": {"request": request},
            },
        ]


class ClusterMembershipSerializer(CustomSerializerTests):
    REQUIRED_FIELDS = []
    NON_REQUIRED_FIELDS = ["id", "user"]

    VALID_DATA = []
    INVALID_DATA = []


class ClusterEventSerializerTests(CustomSerializerTests):
    __test__ = True
    serializer_class = ClusterEventSerializer

    REQUIRED_FIELDS = [
        "event_date",
        "title",
        "event_type",
    ]
    NON_REQUIRED_FIELDS = [
        "id",
        "location",
        "link",
        "description",
        "attendees",
        "status",
        "cluster",
        "created_by",
    ]

    def setUp(self) -> None:
        authenticated_user = UserModelFactory.create(
            is_active=True, email="email1@example.com"
        )
        # Make sure a user is a member of a cluster
        self.cluster = ClusterFactory.create()
        ClusterMembershipFactory.create(cluster=self.cluster, user=authenticated_user)
        request = MagicMock()
        request.user = authenticated_user

        self.VALID_DATA = [
            {
                "data": {
                    "title": "An Event",
                    "event_type": 1,
                    "status": 2,
                    "event_date": "2023-07-17T13:45:51.587Z",
                },
                "lable": "Test valid data",
                "context": {"request": request, "cluster": self.cluster},
            },
            {
                "data": {
                    "title": "A new Event",
                    "event_type": 1,
                    "status": 2,
                    "location": "UI Alumni Building",
                    "event_date": "2023-07-17T13:45:51.587Z",
                },
                "lable": "Test valid data",
                "context": {"request": request, "cluster": self.cluster},
            },
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "title": "An Event",
                    "event_type": 1,
                    "status": 2,
                    "event_date": "2023-07-37",
                },
                "lable": "Test Invalid date type",
                "context": {"request": request, "cluster": self.cluster},
            },
            {
                "data": {
                    "title": "A new Event",
                    "event_type": 1,
                    "status": 5,
                    "location": "UI Alumni Building",
                    "event_date": "2023-07-17T13:45:51.587Z",
                },
                "lable": "Test invalid Data",
                "context": {"request": request, "cluster": self.cluster},
            },
        ]
