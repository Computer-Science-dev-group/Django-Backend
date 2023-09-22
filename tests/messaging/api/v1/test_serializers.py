import uuid
from unittest.mock import MagicMock

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from tests.accounts.test_models import (
    FriendShipFactory,
    FriendShipInvitationFactory,
    UserFriendShipSettingsFactory,
    UserModelFactory,
)
from tests.cluster.test_models import ClusterFactory
from tests.messaging.test_models import (
    CommentFactory,
    DMFactory,
    FileModelFactory,
    PostFactory,
)
from uia_backend.libs.testutils import CustomSerializerTests, get_test_image_file
from uia_backend.messaging.api.v1.serializers import (
    CommentSerializer,
    CreateDMSerializer,
    FileModelSerializer,
    LikeSerializer,
    PostSerializer,
    UpdateDMSerializer,
)
from uia_backend.messaging.models import FileModel


class PostSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = PostSerializer

    REQUIRED_FIELDS = ["title", "content", "file_ids"]
    NON_REQUIRED_FIELDS = [
        "id",
        "is_shared",
        "cluster",
        "created_by",
        "comments",
        "created_datetime",
        "shares",
        "likes",
        "share_comment",
        "liked_by_user",
        "files",
        "ws_channel_name",
    ]

    def setUp(self) -> None:
        authenticated_user = UserModelFactory.create(email="aust@example.com")
        user = UserModelFactory.create()
        friendship_record = FriendShipFactory.create()
        UserFriendShipSettingsFactory.create(
            user=authenticated_user,
            friendship=friendship_record,
            invitation=FriendShipInvitationFactory.create(
                user=authenticated_user,
                created_by=user,
            ),
        )
        UserFriendShipSettingsFactory.create(
            user=user,
            friendship=friendship_record,
            invitation=FriendShipInvitationFactory.create(
                user=user,
                created_by=authenticated_user,
            ),
        )

        request = MagicMock()
        request.user = authenticated_user
        post = PostFactory.create(
            created_by=authenticated_user,
            cluster=ClusterFactory.create(),
        )
        comment = CommentFactory.create(post=post, created_by=authenticated_user)

        # file that has been assigned to a post
        post_file = FileModelFactory.create(
            created_by=authenticated_user,
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            post=post,
        )

        # file that has been assigned to a comment
        comment_file = FileModelFactory.create(
            created_by=authenticated_user,
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            comment=comment,
        )

        # file that has been assigned to a DM
        dm_file = FileModelFactory.create(
            created_by=authenticated_user,
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            dm=DMFactory.create(
                created_by=authenticated_user, friendship=friendship_record
            ),
        )

        # File that was not created by the user
        non_user_file = FileModelFactory.create(
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            created_by=user,
        )

        # cool file
        user_file = FileModelFactory.create(
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            created_by=authenticated_user,
        )

        self.VALID_DATA = [
            {
                "data": {
                    "title": "This is a cool post",
                    "content": "Well hello there",
                    "file_ids": [],
                },
                "context": {"request": request},
                "label": "Test valid data no files attached.",
            },
            {
                "data": {
                    "title": "This is another cool post with a file attached",
                    "content": "Well hello there!!!!!",
                    "file_ids": [user_file.id],
                },
                "context": {"request": request},
                "label": "Test valid data with files attached.",
            },
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "title": "This is another cool post with a file attached",
                    "content": "Well hello there!!!!!",
                    "file_ids": [post_file.id],
                },
                "context": {"request": request},
                "label": "Test invalid data (File has been attached to another post).",
                "error": {
                    "file_ids": [
                        f'Invalid pk "{post_file.id}" - object does not exist.'
                    ]
                },
            },
            {
                "data": {
                    "title": "This is another cool post with a file attached",
                    "content": "Well hello there!!!!!",
                    "file_ids": [comment_file.id],
                },
                "context": {"request": request},
                "label": "Test invalid data (File has been attached to another comment).",
                "error": {
                    "file_ids": [
                        f'Invalid pk "{comment_file.id}" - object does not exist.'
                    ]
                },
            },
            {
                "data": {
                    "title": "This is another cool post with a file attached",
                    "content": "Well hello there!!!!!",
                    "file_ids": [dm_file.id],
                },
                "context": {"request": request},
                "label": "Test invalid data (File has been attached to another DM).",
                "error": {
                    "file_ids": [f'Invalid pk "{dm_file.id}" - object does not exist.']
                },
            },
            {
                "data": {
                    "title": "This is another cool post with a file attached",
                    "content": "Well hello there!!!!!",
                    "file_ids": [non_user_file.id],
                },
                "context": {"request": request},
                "label": "Test invalid data (File does not belong to user).",
                "error": {"file_ids": ["Invaid file id."]},
            },
        ]


class CommentSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = CommentSerializer

    REQUIRED_FIELDS = ["content", "file_ids"]
    NON_REQUIRED_FIELDS = [
        "id",
        "post",
        "cluster",
        "replying",
        "created_by",
        "created_datetime",
        "likes",
        "replies",
        "liked_by_user",
        "files",
    ]

    def setUp(self) -> None:
        authenticated_user = UserModelFactory.create(email="aust@example.com")
        user = UserModelFactory.create()

        request = MagicMock()
        request.user = authenticated_user
        post = PostFactory.create(
            created_by=authenticated_user,
            cluster=ClusterFactory.create(),
        )
        comment = CommentFactory.create(post=post, created_by=authenticated_user)

        # file that has been assigned to a post
        post_file = FileModelFactory.create(
            created_by=authenticated_user,
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            post=post,
        )

        # file that has been assigned to a comment
        comment_file = FileModelFactory.create(
            created_by=authenticated_user,
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            comment=comment,
        )

        # File that was not created by the user
        non_user_file = FileModelFactory.create(
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            created_by=user,
        )

        # cool file
        user_file = FileModelFactory.create(
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            created_by=authenticated_user,
        )

        self.VALID_DATA = [
            {
                "data": {
                    "content": "Well hello there",
                    "file_ids": [],
                },
                "context": {"request": request},
                "label": "Test valid data no files attached.",
            },
            {
                "data": {
                    "content": "Well hello there!!!!!",
                    "file_ids": [user_file.id],
                },
                "context": {"request": request},
                "label": "Test valid data with files attached.",
            },
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "content": "Well hello there!!!!!",
                    "file_ids": [post_file.id],
                },
                "context": {"request": request},
                "label": "Test invalid data (File has been attached to another post).",
                "error": {
                    "file_ids": [
                        f'Invalid pk "{post_file.id}" - object does not exist.'
                    ]
                },
            },
            {
                "data": {
                    "content": "Well hello there!!!!!",
                    "file_ids": [comment_file.id],
                },
                "context": {"request": request},
                "label": "Test invalid data (File has been attached to another comment).",
                "error": {
                    "file_ids": [
                        f'Invalid pk "{comment_file.id}" - object does not exist.'
                    ]
                },
            },
            {
                "data": {
                    "content": "Well hello there!!!!!",
                    "file_ids": [non_user_file.id],
                },
                "context": {"request": request},
                "label": "Test invalid data (File does not belong to user).",
                "error": {"file_ids": ["Invaid file id."]},
            },
        ]


class FileModelSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = FileModelSerializer

    REQUIRED_FIELDS = [
        "file",
        "file_type",
    ]
    NON_REQUIRED_FIELDS = ["id", "created_by", "post", "comment"]

    def setUp(self) -> None:
        file = UploadedFile(
            name="cute.mp4",
            content_type="video/mp4",
            size=1024,
        )
        image = get_test_image_file()
        self.VALID_DATA = [
            {
                "data": {"file_type": FileModel.FILE_TYPE_VIDEO, "file": file},
                "label": "Test valid data",
                "context": None,
            },
            {
                "data": {"file_type": FileModel.FILE_TYPE_IMAGE, "file": image},
                "label": "Test valid data",
                "context": None,
            },
        ]

        large_file = UploadedFile(
            name="cute.mp4",
            content_type="video/mp4",
            size=settings.MAX_MEDIA_UPLOAD_SIZE + 1000,
        )

        self.INVALID_DATA = [
            {
                "data": {"file_type": FileModel.FILE_TYPE_IMAGE, "file": ""},
                "label": "Invalid file",
                "context": None,
                "error": {
                    "file": [
                        "The submitted data was not a file. Check the encoding type on the form."
                    ]
                },
            },
            {
                "data": {"file_type": FileModel.FILE_TYPE_IMAGE, "file": large_file},
                "label": "File too large",
                "context": None,
                "error": {
                    "file": ["File size has exceeded max file upload size (10MB)"]
                },
            },
        ]


class LikeSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = LikeSerializer
    REQUIRED_FIELDS = []
    NON_REQUIRED_FIELDS = ["id", "created_by", "created_datetime"]

    INVALID_DATA = []
    VALID_DATA = []


class CreateDMSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = CreateDMSerializer
    REQUIRED_FIELDS = ["file_ids", "friendship_id"]
    NON_REQUIRED_FIELDS = [
        "id",
        "created_by",
        "files",
        "friendship",
        "content",
        "created_datetime",
        "updated_datetime",
        "edited",
        "replying",
    ]

    def setUp(self) -> None:
        authenticated_user = UserModelFactory.create(email="aust@example.com")

        request = MagicMock()
        request.user = authenticated_user

        user = UserModelFactory.create()

        friendship_record = FriendShipFactory.create()
        UserFriendShipSettingsFactory.create(
            user=authenticated_user,
            friendship=friendship_record,
            invitation=FriendShipInvitationFactory.create(
                user=authenticated_user,
                created_by=user,
            ),
        )
        UserFriendShipSettingsFactory.create(
            user=user,
            friendship=friendship_record,
            invitation=FriendShipInvitationFactory.create(
                user=user,
                created_by=authenticated_user,
            ),
        )

        dm = DMFactory.create(
            created_by=authenticated_user, friendship=friendship_record
        )

        user_file = FileModelFactory.create(
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            created_by=authenticated_user,
        )

        self.VALID_DATA = [
            {
                "data": {
                    "file_ids": [],
                    "replying": None,
                    "content": "Share the",
                    "friendship_id": friendship_record.id,
                },
                "context": {"request": request},
            },
            {
                "data": {
                    "file_ids": [],
                    "replying": dm.id,
                    "content": "National",
                    "friendship_id": friendship_record.id,
                },
                "context": {"request": request},
            },
            {
                "data": {
                    "file_ids": [user_file.id],
                    "replying": dm.id,
                    "content": "Cake",
                    "friendship_id": friendship_record.id,
                },
                "context": {"request": request},
            },
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "file_ids": [user_file.id],
                    "replying": dm.id,
                    "content": "Cake",
                    "friendship_id": uuid.uuid4(),
                },
                "context": {"request": request},
                "label": "Invalid friendship id fails.",
                "error": {"friendship_id": ["Friendship record does not exists."]},
            },
            {
                "data": {
                    "file_ids": [user_file.id],
                    "replying": dm.id,
                    "content": "Cake",
                    "friendship_id": FriendShipFactory.create().id,
                },
                "context": {"request": request},
                "label": "frienship_id not belonging to authenticated user fails",
                "error": {"friendship_id": ["Friendship record does not exists."]},
            },
        ]


class UpdateDMSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = UpdateDMSerializer

    REQUIRED_FIELDS = ["content"]
    NON_REQUIRED_FIELDS = [
        "id",
        "created_by",
        "files",
        "replying",
        "friendship",
        "created_datetime",
        "updated_datetime",
        "edited",
    ]

    VALID_DATA = [
        {
            "data": {
                "content": "Share the",
            },
        },
    ]
    INVALID_DATA = [
        {
            "data": {
                "content": "",
            },
            "label": "Content is cannot be empty.",
            "error": {"content": ["This field may not be blank."]},
        },
    ]
