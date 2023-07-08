from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.urls import reverse
from rest_framework import serializers
from rest_framework.test import APITestCase

from tests.accounts.test_models import UserModelFactory
from tests.cluster.test_models import ClusterFactory, ClusterMembershipFactory
from tests.messaging.test_models import CommentFactory, FileModelFactory, PostFactory
from uia_backend.accounts.api.v1.serializers import UserProfileSerializer
from uia_backend.cluster.constants import (
    UPDATE_CLUSTER_PERMISSION,
    VIEW_CLUSTER_PERMISSION,
)
from uia_backend.libs.permissions import assign_object_permissions
from uia_backend.libs.testutils import get_test_image_file
from uia_backend.messaging.models import Comment, FileModel, Post


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
                        UserProfileSerializer().to_representation(instance=self.user)
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
                },
            },
        )

    def test_list_cluster_posts(self):
        self.client.force_authenticate(self.user)

        # cluster posts (should be listed)
        PostFactory.create_batch(cluster=self.cluster, created_by=self.user, size=3)

        # another clusters posts (shoudld not be listed )
        PostFactory.create_batch(
            cluster=ClusterFactory.create(), created_by=self.user, size=3
        )

        response = self.client.get(path=self.url)
        self.maxDiff = None
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
                            UserProfileSerializer().to_representation(
                                instance=self.user
                            )
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

        self.post = PostFactory.create(created_by=self.user, cluster=self.cluster)

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
                        UserProfileSerializer().to_representation(instance=self.user)
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
                            UserProfileSerializer().to_representation(
                                instance=self.user
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
                        UserProfileSerializer().to_representation(instance=self.user)
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

        self.post = PostFactory.create(created_by=self.user, cluster=self.cluster)
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
                            UserProfileSerializer().to_representation(
                                instance=self.user
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
                        UserProfileSerializer().to_representation(instance=self.user)
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
