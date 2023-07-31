from unittest.mock import MagicMock

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from tests.accounts.test_models import UserModelFactory
from tests.cluster.test_models import ClusterChannelFactory, ClusterFactory
from tests.messaging.test_models import CommentFactory, FileModelFactory, PostFactory
from uia_backend.libs.testutils import CustomSerializerTests, get_test_image_file
from uia_backend.messaging.api.v1.serializers import (
    CommentSerializer,
    FileModelSerializer,
    LikeSerializer,
    PostSerializer,
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
    ]

    def setUp(self) -> None:
        authenticated_user = UserModelFactory.create(email="aust@example.com")
        user = UserModelFactory.create()

        request = MagicMock()
        request.user = authenticated_user

        post = PostFactory.create(
            created_by=authenticated_user,
            cluster=ClusterFactory.create(channel=ClusterChannelFactory.create()),
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
                    "title": "This is a cool post",
                    "content": "Well hello there",
                    "file_ids": [],
                },
                "context": {"request": request},
                "lable": "Test valid data no files attached.",
            },
            {
                "data": {
                    "title": "This is another cool post with a file attached",
                    "content": "Well hello there!!!!!",
                    "file_ids": [user_file.id],
                },
                "context": {"request": request},
                "lable": "Test valid data with files attached.",
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
                "lable": "Test invalid data (File has been attached to another post).",
            },
            {
                "data": {
                    "title": "This is another cool post with a file attached",
                    "content": "Well hello there!!!!!",
                    "file_ids": [comment_file.id],
                },
                "context": {"request": request},
                "lable": "Test invalid data (File has been attached to another comment).",
            },
            {
                "data": {
                    "title": "This is another cool post with a file attached",
                    "content": "Well hello there!!!!!",
                    "file_ids": [non_user_file.id],
                },
                "context": {"request": request},
                "lable": "Test invalid data (File does not belong to user).",
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
            cluster=ClusterFactory.create(channel=ClusterChannelFactory.create()),
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
                "lable": "Test valid data no files attached.",
            },
            {
                "data": {
                    "content": "Well hello there!!!!!",
                    "file_ids": [user_file.id],
                },
                "context": {"request": request},
                "lable": "Test valid data with files attached.",
            },
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "content": "Well hello there!!!!!",
                    "file_ids": [post_file.id],
                },
                "context": {"request": request},
                "lable": "Test invalid data (File has been attached to another post).",
            },
            {
                "data": {
                    "content": "Well hello there!!!!!",
                    "file_ids": [comment_file.id],
                },
                "context": {"request": request},
                "lable": "Test invalid data (File has been attached to another comment).",
            },
            {
                "data": {
                    "content": "Well hello there!!!!!",
                    "file_ids": [non_user_file.id],
                },
                "context": {"request": request},
                "lable": "Test invalid data (File does not belong to user).",
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
                "lable": "Test valid data",
                "context": None,
            },
            {
                "data": {"file_type": FileModel.FILE_TYPE_IMAGE, "file": image},
                "lable": "Test valid data",
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
                "lable": "Invalid file",
                "context": None,
            },
            {
                "data": {"file_type": FileModel.FILE_TYPE_IMAGE, "file": large_file},
                "lable": "File too large",
                "context": None,
            },
        ]


class LikeSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = LikeSerializer
    REQUIRED_FIELDS = []
    NON_REQUIRED_FIELDS = ["id", "created_by", "created_datetime"]

    INVALID_DATA = []
    VALID_DATA = []
