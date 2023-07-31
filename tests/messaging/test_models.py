from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from factory.django import DjangoModelFactory

from tests.accounts.test_models import UserModelFactory
from tests.cluster.test_models import ClusterChannelFactory, ClusterFactory
from uia_backend.messaging.models import (
    Comment,
    FileModel,
    Like,
    Post,
    Share,
    file_upload_location,
)


class PostFactory(DjangoModelFactory):
    title = "The coolest post"
    content = "Du hast gesiegt"

    class Meta:
        model = Post


class CommentFactory(DjangoModelFactory):
    content = "Du kannst siegen"

    class Meta:
        model = Comment


class FileModelFactory(DjangoModelFactory):
    class Meta:
        model = FileModel


class ShareFactory(DjangoModelFactory):
    comment = "Gegrubet seist du imperator"

    class Meta:
        model = Share


class LikeFactory(DjangoModelFactory):
    class Meta:
        model = Like


class LikeTests(TestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        channel = ClusterChannelFactory()
        self.post = PostFactory.create(
            created_by=self.user,
            cluster=ClusterFactory.create(channel=channel),
        )

        self.comment = CommentFactory.create(post=self.post, created_by=self.user)

    def test_unicode(self):
        post_like = LikeFactory.create(post=self.post, created_by=self.user)
        comment_like = LikeFactory.create(comment=self.comment, created_by=self.user)

        self.assertEqual(
            str(post_like), f"User {self.user.email} liked Post {self.post.id}"
        )
        self.assertEqual(
            str(comment_like), f"User {self.user.email} liked Comment {self.comment.id}"
        )

    def test_constraints(self):
        with transaction.atomic():
            with self.assertRaises(IntegrityError) as error:
                LikeFactory.create(
                    post=self.post, comment=self.comment, created_by=self.user
                )

            self.assertEqual(
                str(error.exception),
                "CHECK constraint failed: "
                "messaging_like Must set one and only one of comment or post.",
            )

        with transaction.atomic():
            with self.assertRaises(IntegrityError) as error:
                LikeFactory.create(created_by=self.user)

            self.assertEqual(
                str(error.exception),
                "CHECK constraint failed: "
                "messaging_like Must set one and only one of comment or post.",
            )

        LikeFactory.create(post=self.post, created_by=self.user)
        LikeFactory.create(comment=self.comment, created_by=self.user)


class ShareTests(TestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        channel = ClusterChannelFactory()
        self.post = PostFactory.create(
            created_by=self.user,
            cluster=ClusterFactory.create(channel=channel),
        )

    def test_unicode(self):
        channel = ClusterChannelFactory()
        share = ShareFactory.create(
            created_by=self.user,
            shared_post=self.post,
            new_post=PostFactory.create(
                created_by=self.user, cluster=ClusterFactory.create(channel=channel)
            ),
            cluster=self.post.cluster,
        )

        self.assertEqual(
            str(share), f"User {self.user.email} shared post {self.post.id}"
        )


class FileUploadLocationTest(TestCase):
    def test_method(self):
        user = UserModelFactory.create()

        file_record = FileModelFactory.create(
            file_type=FileModel.FILE_TYPE_IMAGE, file=""
        )

        self.assertEqual(
            file_upload_location(instance=file_record, filename="image.png"),
            f"media/{timezone.now().date().isoformat()}/image.png",
        )

        file_record = FileModelFactory.create(
            file_type=FileModel.FILE_TYPE_IMAGE, file="", created_by=user
        )

        self.assertEqual(
            file_upload_location(instance=file_record, filename="image.png"),
            f"users/{user.id}/media/image.png",
        )
