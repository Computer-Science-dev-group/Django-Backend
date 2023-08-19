import uuid
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.urls import reverse
from rest_framework import serializers
from rest_framework.test import APITestCase

from tests.accounts.test_models import (
    FriendShipFactory,
    FriendShipInvitationFactory,
    UserFriendShipSettingsFactory,
    UserModelFactory,
)
from tests.cluster.test_models import ClusterFactory, ClusterMembershipFactory
from tests.messaging.test_models import (
    CommentFactory,
    DMFactory,
    FileModelFactory,
    LikeFactory,
    PostFactory,
)
from uia_backend.accounts.api.v1.serializers import ProfileSerializer
from uia_backend.cluster.constants import (
    UPDATE_CLUSTER_PERMISSION,
    VIEW_CLUSTER_PERMISSION,
)
from uia_backend.libs.permissions import assign_object_permissions
from uia_backend.libs.testutils import get_test_image_file
from uia_backend.messaging.api.v1.serializers import PostSerializer
from uia_backend.messaging.constants import (
    CENT_EVENT_POST_LIKE_CREATED,
    CENT_EVENT_POST_LIKE_DELETED,
)
from uia_backend.messaging.models import DM, Comment, FileModel, Like, Post


class PostListAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        self.cluster = ClusterFactory.create()
        ClusterMembershipFactory(
            user=self.user,
            cluster=self.cluster,
        )
        self.file = FileModelFactory.create(
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            created_by=self.user,
        )
        self.url = reverse("messaging_api_v1:cluster_post_list", args=[self.cluster.id])

        assign_object_permissions(
            permissions=[VIEW_CLUSTER_PERMISSION, UPDATE_CLUSTER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

    def test_fails_for_unauthenticated_user(self):
        data = {
            "title": "This is another cool post with a file attached",
            "content": "Well hello there!!!!!",
            "file_ids": [self.file.id],
        }

        response = self.client.post(data=data, path=self.url, format="multipart")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_post_fails_for_non_cluster_member(self):
        user = UserModelFactory.create(email="micope@example.com")
        self.client.force_authenticate(user=user)

        data = {
            "title": "This is another cool post with a file attached",
            "content": "Well hello there!!!!!",
            "file_ids": [self.file.id],
        }

        response = self.client.post(data=data, path=self.url, format="multipart")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 403,
                "data": {
                    "detail": "You do not have permission to perform this action."
                },
            },
        )

    def test_post_fails_if_medai_file_has_already_been_assigned(self):
        self.client.force_authenticate(self.user)
        post = PostFactory.create(
            created_by=self.user,
            cluster=self.cluster,
        )

        comment = CommentFactory.create(post=post, created_by=self.user)

        # file that has been assigned to a post
        post_file = FileModelFactory.create(
            created_by=self.user,
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            post=post,
        )

        # file that has been assigned to a comment
        comment_file = FileModelFactory.create(
            created_by=self.user,
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            comment=comment,
        )

        # test post for file assigned to a post
        response = self.client.post(
            path=self.url,
            data={
                "title": "Du hast",
                "content": "Uber Gigben",
                "file_ids": [str(post_file.id)],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "file_ids": [
                        f'Invalid pk "{post_file.id}" - object does not exist.'
                    ]
                },
            },
        )

        # ensure that no records where created
        self.assertEqual(Post.objects.exclude(id=post.id).count(), 0)

        # test post for file assigned to a comment
        response = self.client.post(
            path=self.url,
            data={
                "title": "Du hast",
                "content": "Uber Gigben",
                "file_ids": [str(comment_file.id)],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "file_ids": [
                        f'Invalid pk "{comment_file.id}" - object does not exist.'
                    ]
                },
            },
        )

        # ensure that no records where created
        self.assertEqual(Post.objects.exclude(id=post.id).count(), 0)

    def test_post_fails_if_media_file_was_not_created_by_user(self):
        self.client.force_authenticate(self.user)
        user = UserModelFactory.create(email="digi@example.com")

        another_users_file = FileModelFactory.create(
            created_by=user,
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
        )

        response = self.client.post(
            path=self.url,
            data={
                "title": "Du hast",
                "content": "Uber Gigben",
                "file_ids": [another_users_file.id],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"status": "Error", "code": 400, "data": {"file_ids": ["Invaid file id."]}},
        )

        # ensure that no records where created
        self.assertEqual(Post.objects.all().count(), 0)

    def test_post_successful(self):
        self.client.force_authenticate(user=self.user)
        files = FileModelFactory.create_batch(
            created_by=self.user,
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            size=3,
        )

        response = self.client.post(
            path=self.url,
            data={
                "title": "Du hast",
                "content": "Uber Gigben",
                "file_ids": [file.id for file in files],
            },
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(Post.objects.all().count(), 1)
        post = Post.objects.all().first()

        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 201,
                "data": {
                    "id": str(post.id),
                    "title": "Du hast",
                    "content": "Uber Gigben",
                    "is_shared": False,
                    "cluster": str(self.cluster.id),
                    "created_by": dict(
                        ProfileSerializer().to_representation(instance=self.user)
                    ),
                    "comments": 0,
                    "created_datetime": serializers.DateTimeField().to_representation(
                        value=post.created_datetime
                    ),
                    "shares": 0,
                    "likes": 0,
                    "share_comment": None,
                    "liked_by_user": False,
                    "files": [
                        {"file": f"http://testserver/media/{file.file.name}"}
                        for file in files
                    ],
                    "ws_channel_name": f"$posts:{post.id}",
                },
            },
        )

    def test_list_cluster_posts(self):
        self.client.force_authenticate(self.user)

        # cluster posts (should be listed)
        [
            PostFactory.create(cluster=self.cluster, created_by=self.user)
            for i in range(3)
        ]

        # another clusters posts (shoudld not be listed )
        [
            PostFactory.create(
                cluster=ClusterFactory.create(),
                created_by=self.user,
            )
            for i in range(3)
        ]

        response = self.client.get(path=self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 3,
                "next": None,
                "previous": None,
                "status": "Success",
                "code": 200,
                "data": [
                    {
                        "id": str(post.id),
                        "title": post.title,
                        "content": post.content,
                        "is_shared": False,
                        "cluster": str(self.cluster.id),
                        "created_by": dict(
                            ProfileSerializer().to_representation(instance=self.user)
                        ),
                        "comments": 0,
                        "created_datetime": serializers.DateTimeField().to_representation(
                            value=post.created_datetime
                        ),
                        "shares": 0,
                        "likes": 0,
                        "share_comment": None,
                        "liked_by_user": False,
                        "files": [],
                        "ws_channel_name": f"$posts:{post.id}",
                    }
                    for post in Post.objects.filter(cluster=self.cluster).order_by(
                        "-created_datetime"
                    )
                ],
            },
        )


class PostDetailsAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        self.cluster = ClusterFactory.create()

        ClusterMembershipFactory(user=self.user, cluster=self.cluster)

        self.file = FileModelFactory.create(
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            created_by=self.user,
        )

        self.post = PostFactory.create(
            created_by=self.user,
            cluster=self.cluster,
        )

        self.url = reverse(
            "messaging_api_v1:cluster_post_details",
            args=[self.cluster.id, self.post.id],
        )

        assign_object_permissions(
            permissions=[VIEW_CLUSTER_PERMISSION, UPDATE_CLUSTER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

    def test_fails_for_unauthenticated_user(self):
        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_retrieve_fails_for_non_cluster_member(self):
        user = UserModelFactory.create(email="micope@example.com")
        self.client.force_authenticate(user=user)

        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 403,
                "data": {
                    "detail": "You do not have permission to perform this action."
                },
            },
        )

    def test_retrieve_successfully(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.post.id),
                    "title": self.post.title,
                    "content": self.post.content,
                    "is_shared": False,
                    "cluster": str(self.cluster.id),
                    "created_by": dict(
                        ProfileSerializer().to_representation(instance=self.user)
                    ),
                    "comments": 0,
                    "created_datetime": serializers.DateTimeField().to_representation(
                        value=self.post.created_datetime
                    ),
                    "shares": 0,
                    "likes": 0,
                    "share_comment": None,
                    "liked_by_user": False,
                    "files": [],
                    "ws_channel_name": f"$posts:{self.post.id}",
                },
            },
        )

    def test_delete_fails_for_non_cluster_member(self):
        user = UserModelFactory.create(email="micope@example.com")
        self.client.force_authenticate(user=user)

        response = self.client.delete(path=self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 403,
                "data": {
                    "detail": "You do not have permission to perform this action."
                },
            },
        )

    def test_delete_fails_for_cluster_members_but_not_creator(self):
        user = UserModelFactory.create(email="member@example.com")

        ClusterMembershipFactory(user=user, cluster=self.cluster)

        self.client.force_authenticate(user=user)

        assign_object_permissions(
            permissions=[VIEW_CLUSTER_PERMISSION, UPDATE_CLUSTER_PERMISSION],
            assignee=user,
            obj=self.cluster,
        )

        response = self.client.delete(path=self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 403,
                "data": {
                    "detail": "You do not have permission to perform this action."
                },
            },
        )

    def test_delete_successful(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(path=self.url)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, None)

        self.assertFalse(Post.objects.all().exists())


class LikePostAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        self.cluster = ClusterFactory.create()

        ClusterMembershipFactory(user=self.user, cluster=self.cluster)

        self.file = FileModelFactory.create(
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            created_by=self.user,
        )

        self.post = PostFactory.create(
            created_by=self.user,
            cluster=self.cluster,
        )

        self.url = reverse(
            "messaging_api_v1:post_like",
            args=[self.cluster.id, self.post.id],
        )

        assign_object_permissions(
            permissions=[VIEW_CLUSTER_PERMISSION, UPDATE_CLUSTER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

    def test_post_fails_for_unauthenticated_user(self):
        response = self.client.post(path=self.url, data={})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_delete_fails_for_unauthenticated_user(self):
        response = self.client.delete(path=self.url, data={})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_post_fails_for_non_cluster_member(self):
        user = UserModelFactory.create(email="micope@example.com")
        self.client.force_authenticate(user=user)

        response = self.client.post(path=self.url, data={})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 403,
                "data": {
                    "detail": "You do not have permission to perform this action."
                },
            },
        )

    def test_delete_fails_non_cluster_member(self):
        user = UserModelFactory.create(email="micope@example.com")
        self.client.force_authenticate(user=user)

        LikeFactory.create(post=self.post, created_by=self.user)
        response = self.client.delete(path=self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 403,
                "data": {
                    "detail": "You do not have permission to perform this action."
                },
            },
        )

    def test_post_behaviour_if_user_already_liked_post(self):
        """Test that post does not fail if user already liked the post."""
        self.client.force_authenticate(self.user)
        like = LikeFactory.create(post=self.post, created_by=self.user)

        response = self.client.post(path=self.url, data={})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Like.objects.filter(post=self.post, created_by=self.user).count(), 1
        )
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 201,
                "data": {
                    "id": str(like.id),
                    "created_by": dict(
                        ProfileSerializer().to_representation(instance=like.created_by)
                    ),
                    "created_datetime": serializers.DateTimeField().to_representation(
                        value=like.created_datetime
                    ),
                },
            },
        )

    def test_create_like_successfully(self):
        self.client.force_authenticate(self.user)

        with patch(
            "uia_backend.libs.centrifugo.CentrifugoConnector.broadcast_event"
        ) as mock_publish_centrifugo_event:
            response = self.client.post(path=self.url, data={})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Like.objects.filter(post=self.post, created_by=self.user).count(), 1
        )
        like = Like.objects.all().first()
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 201,
                "data": {
                    "id": str(like.id),
                    "created_by": dict(
                        ProfileSerializer().to_representation(instance=like.created_by)
                    ),
                    "created_datetime": serializers.DateTimeField().to_representation(
                        value=like.created_datetime
                    ),
                },
            },
        )

        request = MagicMock()
        request.user = self.user

        mock_publish_centrifugo_event.assert_called_once_with(
            event_name=CENT_EVENT_POST_LIKE_CREATED,
            channels=[like.post.channel_name, like.post.cluster.channel_name],
            event_data=dict(
                PostSerializer(context={"request": request}).to_representation(
                    instance=like.post
                )
            ),
        )

    def test_delete_like_successfully(self):
        self.client.force_authenticate(self.user)
        like = LikeFactory.create(post=self.post, created_by=self.user)

        with patch(
            "uia_backend.libs.centrifugo.CentrifugoConnector.broadcast_event"
        ) as mock_publish_centrifugo_event:
            response = self.client.delete(path=self.url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Like.objects.filter(id=like.id).exists())

        request = MagicMock()
        request.user = self.user

        self.post.refresh_from_db()
        mock_publish_centrifugo_event.assert_called_once_with(
            event_name=CENT_EVENT_POST_LIKE_DELETED,
            channels=[self.post.channel_name, self.post.cluster.channel_name],
            event_data=dict(
                PostSerializer(context={"request": request}).to_representation(
                    instance=self.post
                )
            ),
        )

    def test_delete_like_fails_if_user_has_not_liked_post(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(path=self.url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"status": "Error", "code": 404, "data": {"detail": "Not found."}},
        )


class CommentListAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        self.cluster = ClusterFactory.create()

        ClusterMembershipFactory(user=self.user, cluster=self.cluster)

        self.file = FileModelFactory.create(
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            created_by=self.user,
        )

        self.post = PostFactory.create(created_by=self.user, cluster=self.cluster)

        self.url = reverse(
            "messaging_api_v1:post_list_comments", args=[self.cluster.id, self.post.id]
        )

        assign_object_permissions(
            permissions=[VIEW_CLUSTER_PERMISSION, UPDATE_CLUSTER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

    def test_fails_for_unauthenticated_user(self):
        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_get_fails_for_non_cluster_member(self):
        user = UserModelFactory.create(email="micope@example.com")
        self.client.force_authenticate(user=user)

        response = self.client.get(
            path=self.url,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 403,
                "data": {
                    "detail": "You do not have permission to perform this action."
                },
            },
        )

    def test_post_fails_for_non_cluster_member(self):
        user = UserModelFactory.create(email="micope@example.com")
        self.client.force_authenticate(user=user)

        response = self.client.post(
            path=self.url,
            data={"content": "Cool comment", "file_ids": [str(self.file.id)]},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 403,
                "data": {
                    "detail": "You do not have permission to perform this action."
                },
            },
        )

    def test_list_comments_successfully(self):
        self.client.force_authenticate(self.user)

        another_user = UserModelFactory.create(email="another@example.com")
        another_post = PostFactory.create(
            created_by=another_user,
            cluster=self.cluster,
        )

        # post comments (should be listed)
        listed_comments = CommentFactory.create_batch(
            post=self.post, created_by=self.user, size=3
        )
        listed_comments.extend(
            CommentFactory.create_batch(post=self.post, created_by=another_user, size=3)
        )

        # another post comments (should not be listed)
        CommentFactory.create_batch(post=another_post, created_by=self.user, size=3)
        CommentFactory.create_batch(post=another_post, created_by=another_user, size=3)

        # reply comments (should not be listed)
        CommentFactory.create_batch(
            post=self.post,
            created_by=another_user,
            replying=CommentFactory.create(post=another_post, created_by=self.user),
            size=3,
        )

        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 6,
                "next": None,
                "previous": None,
                "status": "Success",
                "code": 200,
                "data": [
                    {
                        "id": str(comment.id),
                        "post": str(self.post.id),
                        "replying": None,
                        "created_by": dict(
                            ProfileSerializer().to_representation(
                                instance=comment.created_by
                            )
                        ),
                        "created_datetime": serializers.DateTimeField().to_representation(
                            value=comment.created_datetime
                        ),
                        "likes": 0,
                        "replies": 0,
                        "liked_by_user": False,
                        "content": comment.content,
                        "files": [],
                    }
                    for comment in Comment.objects.filter(
                        id__in=[_.id for _ in listed_comments]
                    ).order_by("-created_datetime")
                ],
            },
        )

    def test_create_comment_successfully(self):
        self.client.force_authenticate(self.user)

        data = {"content": "Standing on sacrad ground", "file_ids": [str(self.file.id)]}

        response = self.client.post(path=self.url, data=data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.filter(post=self.post).count(), 1)
        comment = Comment.objects.filter(post=self.post).first()

        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 201,
                "data": {
                    "id": str(comment.id),
                    "post": str(self.post.id),
                    "replying": None,
                    "created_by": dict(
                        ProfileSerializer().to_representation(instance=self.user)
                    ),
                    "created_datetime": serializers.DateTimeField().to_representation(
                        value=comment.created_datetime
                    ),
                    "likes": 0,
                    "replies": 0,
                    "liked_by_user": False,
                    "content": comment.content,
                    "files": [
                        {"file": f"http://testserver/media/{self.file.file.name}"}
                    ],
                },
            },
        )


class RepliesListAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        self.cluster = ClusterFactory.create()

        ClusterMembershipFactory(user=self.user, cluster=self.cluster)

        self.file = FileModelFactory.create(
            file_type=FileModel.FILE_TYPE_IMAGE,
            file=get_test_image_file(),
            created_by=self.user,
        )

        self.post = PostFactory.create(
            created_by=self.user,
            cluster=self.cluster,
        )
        self.comment = CommentFactory.create(
            created_by=self.user,
            post=self.post,
        )

        self.url = reverse(
            "messaging_api_v1:comment_reply_list",
            args=[self.cluster.id, self.post.id, self.comment.id],
        )

        assign_object_permissions(
            permissions=[VIEW_CLUSTER_PERMISSION, UPDATE_CLUSTER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

        self.maxDiff = None

    def test_fails_for_unauthenticated_user(self):
        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_get_fails_for_non_cluster_member(self):
        user = UserModelFactory.create(email="micope@example.com")
        self.client.force_authenticate(user=user)

    def test_post_fails_for_non_cluster_member(self):
        user = UserModelFactory.create(email="micope@example.com")
        self.client.force_authenticate(user=user)

        response = self.client.post(
            path=self.url,
            data={"content": "Cool comment", "file_ids": [str(self.file.id)]},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 403,
                "data": {
                    "detail": "You do not have permission to perform this action."
                },
            },
        )

        response = self.client.get(
            path=self.url,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 403,
                "data": {
                    "detail": "You do not have permission to perform this action."
                },
            },
        )

    def test_list_comment_replies_successfully(self):
        self.client.force_authenticate(self.user)

        another_user = UserModelFactory.create(email="another@example.com")
        another_comment = CommentFactory.create(
            created_by=another_user,
            post=self.post,
        )

        # comment replies (should be listed)
        listed_replies = CommentFactory.create_batch(
            post=self.post,
            created_by=self.user,
            replying=self.comment,
            size=3,
        )
        listed_replies.extend(
            CommentFactory.create_batch(
                post=self.post, created_by=another_user, replying=self.comment, size=3
            )
        )

        # another comments replies (should not be listed)
        CommentFactory.create_batch(
            post=self.post, replying=another_comment, created_by=self.user, size=3
        )
        CommentFactory.create_batch(
            post=self.post, replying=another_comment, created_by=another_user, size=3
        )

        # non reply comments (should not be listed)
        CommentFactory.create_batch(post=self.post, created_by=self.user, size=3)
        CommentFactory.create_batch(post=self.post, created_by=another_user, size=3)

        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 6,
                "next": None,
                "previous": None,
                "status": "Success",
                "code": 200,
                "data": [
                    {
                        "id": str(comment.id),
                        "post": str(self.post.id),
                        "replying": str(self.comment.id),
                        "created_by": dict(
                            ProfileSerializer().to_representation(
                                instance=comment.created_by
                            )
                        ),
                        "created_datetime": serializers.DateTimeField().to_representation(
                            value=comment.created_datetime
                        ),
                        "likes": 0,
                        "replies": 0,
                        "liked_by_user": False,
                        "content": comment.content,
                        "files": [],
                    }
                    for comment in Comment.objects.filter(
                        id__in=[reply.id for reply in listed_replies]
                    ).order_by("-created_datetime")
                ],
            },
        )

    def test_create_reply_successfuly(self):
        self.client.force_authenticate(self.user)

        data = {"content": "Standing on sacrad ground", "file_ids": [str(self.file.id)]}

        response = self.client.post(path=self.url, data=data)

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            Comment.objects.filter(
                post=self.post,
                replying=self.comment,
            ).count(),
            1,
        )

        comment = Comment.objects.filter(post=self.post, replying=self.comment).first()

        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 201,
                "data": {
                    "id": str(comment.id),
                    "post": str(self.post.id),
                    "replying": str(self.comment.id),
                    "created_by": dict(
                        ProfileSerializer().to_representation(instance=self.user)
                    ),
                    "created_datetime": serializers.DateTimeField().to_representation(
                        value=comment.created_datetime
                    ),
                    "likes": 0,
                    "replies": 0,
                    "liked_by_user": False,
                    "content": comment.content,
                    "files": [
                        {"file": f"http://testserver/media/{self.file.file.name}"}
                    ],
                },
            },
        )


class FileUploadAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        self.url = reverse("messaging_api_v1:file_upload")

    def test_fails_for_unauthenticated_user(self):
        data = {
            "file": get_test_image_file(),
            "file _type": FileModel.FILE_TYPE_IMAGE,
        }

        response = self.client.post(data=data, path=self.url, format="multipart")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_file_upload_sucessfully(self):
        self.client.force_authenticate(self.user)

        data = {
            "file": UploadedFile(
                file=SimpleUploadedFile(
                    name="cute.mp4",
                    content=b"wellhollo",
                    content_type="video/mp4",
                ),
                name="cute.mp4",
                content_type="video/mp4",
                size=1000,
            ),
            "file_type": FileModel.FILE_TYPE_VIDEO,
        }

        response = self.client.post(data=data, path=self.url, format="multipart")

        self.assertEqual(response.status_code, 201)

        file_query = FileModel.objects.all()
        self.assertEqual(file_query.count(), 1)

        file = file_query.first()

        self.assertEqual(file.created_by, self.user)
        self.assertEqual(file.file_type, FileModel.FILE_TYPE_VIDEO)
        self.assertIsNone(file.post)
        self.assertIsNone(file.comment)

        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 201,
                "data": {
                    "id": str(file.id),
                    "file_type": 1,
                    "file": f"http://testserver/media/{file.file.name}",
                    "created_by": str(self.user.id),
                    "post": None,
                    "comment": None,
                },
            },
        )


class DMCreateAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.authenticated_user = UserModelFactory.create()
        self.user = UserModelFactory.create(email="miscope@example.com")
        self.url = reverse("messaging_api_v1:create_dm")
        self.friendship_record = FriendShipFactory.create()
        UserFriendShipSettingsFactory.create(
            user=self.authenticated_user,
            friendship=self.friendship_record,
            invitation=FriendShipInvitationFactory.create(
                user=self.authenticated_user,
                created_by=self.user,
            ),
        )
        UserFriendShipSettingsFactory.create(
            user=self.user,
            friendship=self.friendship_record,
            invitation=FriendShipInvitationFactory.create(
                user=self.user,
                created_by=self.authenticated_user,
            ),
        )

    def test_create_dm_fails_when_user_is_authenticated(self):
        """Create DM fails for unathenticated user."""

        data = {
            "file_ids": [],
            "replying": None,
            "content": "Donate the",
            "friendship_id": str(self.friendship_record.id),
        }

        response = self.client.post(data=data, path=self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )
        self.assertEqual(DM.objects.all().count(), 0)

    def test_create_dm_fails_for_invalid_frienship_id(self):
        """Create DM fails for invalid friendhip id."""

        self.client.force_authenticate(self.authenticated_user)

        # test for non-existing uuid
        data = {
            "file_ids": [],
            "replying": None,
            "content": "National",
            "friendship_id": str(uuid.uuid4()),
        }

        response = self.client.post(data=data, path=self.url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "friendship_id": ["Friendship record does not exists."],
                },
            },
        )

        self.assertEqual(DM.objects.all().count(), 0)

        # test for frienship that is not associated to users
        data = {
            "file_ids": [],
            "replying": None,
            "content": "MoiMoi",
            "friendship_id": str(FriendShipFactory.create().id),
        }

        response = self.client.post(data=data, path=self.url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "friendship_id": ["Friendship record does not exists."],
                },
            },
        )

        self.assertEqual(DM.objects.all().count(), 0)

    def test_create_dm_successfully(self):
        """Create dm successfully create message and send centrifugo events."""

        self.client.force_authenticate(self.authenticated_user)

        data = {
            "file_ids": [],
            "replying": None,
            "content": "Share the national cake",
            "friendship_id": str(self.friendship_record.id),
        }

        response = self.client.post(data=data, path=self.url)

        self.assertEqual(response.status_code, 201)

        dm_query = DM.objects.filter(created_by=self.authenticated_user)
        self.assertEqual(dm_query.count(), 1)
        dm = dm_query.first()
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 201,
                "data": {
                    "id": str(dm.id),
                    "replying": None,
                    "created_by": dict(
                        ProfileSerializer().to_representation(
                            instance=self.authenticated_user
                        )
                    ),
                    "friendship": str(self.friendship_record.id),
                    "content": "Share the national cake",
                    "created_datetime": serializers.DateTimeField().to_representation(
                        value=dm.created_datetime
                    ),
                    "updated_datetime": serializers.DateTimeField().to_representation(
                        value=dm.updated_datetime
                    ),
                    "edited": False,
                    "files": [],
                },
            },
        )


class ListDMAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.authenticated_user = UserModelFactory.create()
        self.user = UserModelFactory.create(email="miscope@example.com")
        self.friendship_record = FriendShipFactory.create()
        self.url = reverse("messaging_api_v1:list_dm", args=[self.friendship_record.id])

        UserFriendShipSettingsFactory.create(
            user=self.authenticated_user,
            friendship=self.friendship_record,
            invitation=FriendShipInvitationFactory.create(
                user=self.authenticated_user,
                created_by=self.user,
            ),
        )
        UserFriendShipSettingsFactory.create(
            user=self.user,
            friendship=self.friendship_record,
            invitation=FriendShipInvitationFactory.create(
                user=self.user,
                created_by=self.authenticated_user,
            ),
        )

    def test_list_dms_fails_when_user_is_authenticated(self):
        """List DMs fails for unathenticated user."""

        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_list_dms_successfully(self):
        """List dms returns dm sent though friendship connection"""

        self.client.force_authenticate(self.authenticated_user)

        # dms sent by user though friendship  (Should be listed)
        dm_created_by_user = DMFactory.create_batch(
            created_by=self.authenticated_user,
            friendship=self.friendship_record,
            size=5,
        )

        # dms sent to user though friendship (Should be listed)
        dms_sent_to_user = DMFactory.create_batch(
            created_by=self.user,
            friendship=self.friendship_record,
            size=5,
        )

        # dms sent by user though friendship (Should not be listed)
        dms_sent_by_user_through_another_friendship = DMFactory.create_batch(
            created_by=self.authenticated_user,
            friendship=FriendShipFactory.create(),
            size=5,
        )

        # dms sent to user though friendship (Should not be listed)
        dms_sent_to_user_through_another_friendship = DMFactory.create_batch(
            created_by=self.user,
            friendship=FriendShipFactory.create(),
            size=5,
        )

        response = self.client.get(path=self.url)
        self.maxDiff = None
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "next": None,
                "previous": None,
                "count": 10,
                "data": [
                    {
                        "id": str(dm.id),
                        "replying": dm.replying,
                        "created_by": dict(
                            ProfileSerializer().to_representation(
                                instance=dm.created_by
                            )
                        ),
                        "friendship": str(dm.friendship_id),
                        "content": dm.content,
                        "created_datetime": serializers.DateTimeField().to_representation(
                            value=dm.created_datetime
                        ),
                        "updated_datetime": serializers.DateTimeField().to_representation(
                            value=dm.updated_datetime
                        ),
                        "edited": dm.edited,
                        "files": [],
                    }
                    for dm in DM.objects.filter(
                        id__in=[dm.id for dm in dm_created_by_user + dms_sent_to_user]
                    )
                    .exclude(
                        id__in=[
                            dm.id
                            for dm in dms_sent_by_user_through_another_friendship
                            + dms_sent_to_user_through_another_friendship
                        ]
                    )
                    .order_by("-created_datetime")
                ],
            },
        )


class RetrieveUpdateDMAPIView(APITestCase):
    def setUp(self) -> None:
        self.authenticated_user = UserModelFactory.create()
        self.user = UserModelFactory.create(email="miscope@example.com")
        self.friendship_record = FriendShipFactory.create()

        UserFriendShipSettingsFactory.create(
            user=self.authenticated_user,
            friendship=self.friendship_record,
            invitation=FriendShipInvitationFactory.create(
                user=self.authenticated_user,
                created_by=self.user,
            ),
        )
        UserFriendShipSettingsFactory.create(
            user=self.user,
            friendship=self.friendship_record,
            invitation=FriendShipInvitationFactory.create(
                user=self.user,
                created_by=self.authenticated_user,
            ),
        )

        self.dm = DMFactory.create(
            created_by=self.authenticated_user,
            friendship=self.friendship_record,
            content="Edited message",
        )

        self.url = reverse(
            "messaging_api_v1:dm_details", args=[self.friendship_record.id, self.dm.id]
        )

    def test_retrieve_dm_fails_when_user_is_unauthenticated(self):
        """Retrieve DM fails for unauthenticated user."""

        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_update_dm_fails_when_user_is_unauthenticated(self):
        """Update DM fails for unauthenticated user."""

        data = {"content": "Edited message"}
        response = self.client.put(path=self.url, data=data)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_delete_dm_fails_when_user_is_unauthenticated(self):
        """Delete DM fails for unauthenticated user."""

        response = self.client.delete(path=self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_update_fails_if_user_is_not_dm_creator(self):
        """Update fails if user is not DM creator."""

        self.client.force_authenticate(self.user)
        data = {"content": "Domine libra nos"}
        response = self.client.put(path=self.url, data=data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 404,
                "data": {"detail": "Not found."},
            },
        )

        self.dm.refresh_from_db()
        self.assertNotEqual(self.dm.content, "Domine libra nos")

    def test_delete_fails_if_user_is_not_dm_creator(self):
        """Delete fails if user is not DM creator."""

        self.client.force_authenticate(self.user)
        data = {"content": "Domine libra nos"}
        response = self.client.put(path=self.url, data=data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 404,
                "data": {"detail": "Not found."},
            },
        )

        self.dm.refresh_from_db()
        self.assertIsNotNone(self.dm)

    def test_retrieve_dm_successfully(self):
        """Retrieve DM returns dm data."""

        self.client.force_authenticate(self.authenticated_user)

        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.dm.id),
                    "replying": None,
                    "created_by": dict(
                        ProfileSerializer().to_representation(
                            instance=self.dm.created_by
                        )
                    ),
                    "friendship": str(self.dm.friendship_id),
                    "content": self.dm.content,
                    "created_datetime": serializers.DateTimeField().to_representation(
                        value=self.dm.created_datetime
                    ),
                    "updated_datetime": serializers.DateTimeField().to_representation(
                        value=self.dm.updated_datetime
                    ),
                    "edited": False,
                    "files": [],
                },
            },
        )

    def test_update_dm_successfully(self):
        """Update DM updates dm content, sets edited to true and sends centrifugo event."""

        self.client.force_authenticate(self.authenticated_user)

        data = {"content": "Domine libra nos"}
        with patch(
            "uia_backend.libs.centrifugo.CentrifugoConnector.broadcast_event"
        ) as mock_publish_centrifugo_event:
            response = self.client.put(path=self.url, data=data)

        self.assertEqual(response.status_code, 200)
        self.dm.refresh_from_db()
        self.assertEqual(self.dm.content, "Domine libra nos")
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.dm.id),
                    "replying": None,
                    "created_by": dict(
                        ProfileSerializer().to_representation(
                            instance=self.dm.created_by
                        )
                    ),
                    "friendship": str(self.dm.friendship_id),
                    "content": "Domine libra nos",
                    "created_datetime": serializers.DateTimeField().to_representation(
                        value=self.dm.created_datetime
                    ),
                    "updated_datetime": serializers.DateTimeField().to_representation(
                        value=self.dm.updated_datetime
                    ),
                    "edited": True,
                    "files": [],
                },
            },
        )

        mock_publish_centrifugo_event.assert_called_once()

    def test_delete_dm_successfully(self):
        """Delete dm removes record from db and sends centrifugo event."""

        self.client.force_authenticate(self.authenticated_user)
        with patch(
            "uia_backend.libs.centrifugo.CentrifugoConnector.broadcast_event"
        ) as mock_publish_centrifugo_event:
            response = self.client.delete(path=self.url)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(DM.objects.count(), 0)
        self.assertEqual(response.data, None)
        mock_publish_centrifugo_event.assert_called_once()
