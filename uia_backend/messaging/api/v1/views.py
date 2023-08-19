from typing import Any

from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, permissions
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from uia_backend.cluster.models import Cluster
from uia_backend.libs.centrifugo import CentrifugoConnector
from uia_backend.messaging.api.v1.permission import ClusterPostPermission
from uia_backend.messaging.api.v1.serializers import (
    CommentSerializer,
    CreateDMSerializer,
    FileModelSerializer,
    LikeSerializer,
    PostSerializer,
    UpdateDMSerializer,
)
from uia_backend.messaging.constants import (
    CENT_EVENT_DM_CREATED,
    CENT_EVENT_DM_EDITED,
    CENT_EVENT_POST_DELETED,
    CENT_EVENT_POST_LIKE_CREATED,
    CENT_EVENT_POST_LIKE_DELETED,
)
from uia_backend.messaging.models import DM, Comment, Like, Post


class PostListAPIView(generics.ListCreateAPIView):
    """List/create posts in a cluster."""

    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, ClusterPostPermission]

    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ["created_datetime"]
    search_fields = ["content", "title"]
    ordering = ["-created_datetime"]

    def get_object(self) -> Cluster:
        cluster = get_object_or_404(Cluster, id=self.kwargs["cluster_id"])
        self.check_object_permissions(request=self.request, obj=cluster)
        return cluster

    def get_queryset(self) -> QuerySet[Post]:
        cluster = self.get_object()
        return (
            Post.objects.select_related("created_by")
            .prefetch_related("files", "likes", "shares")
            .filter(cluster=cluster)
        )

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        self.get_object()
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer) -> None:
        serializer.save(
            created_by=self.request.user,
            cluster_id=self.kwargs["cluster_id"],
        )


class PostDetailsAPIView(generics.RetrieveDestroyAPIView):
    """Retrieve/Delete post."""

    serializer_class = PostSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        ClusterPostPermission,
    ]

    def get_object(self) -> Post:
        post = get_object_or_404(
            Post.objects.prefetch_related("cluster"),
            id=self.kwargs["post_id"],
            cluster_id=self.kwargs["cluster_id"],
        )

        # NOTE: (Joseph) for now lets handle it this way
        # so only a user can delete their post
        if (post.created_by_id != self.request.user.id) and (
            self.request.method.upper() == "DELETE"
        ):
            self.permission_denied(request=self.request)

        self.check_object_permissions(request=self.request, obj=post.cluster)

        return post

    def perform_destroy(self, instance: Post) -> None:
        channels = [instance.channel_name, instance.cluster.channel_name]
        data_to_broadcast = {
            "event_name": CENT_EVENT_POST_DELETED,
            "channels": channels,
            "event_data": dict(
                PostSerializer(context={"request": self.request}).to_representation(
                    instance=instance
                )
            ),
        }

        super().perform_destroy(instance)
        CentrifugoConnector().broadcast_event(**data_to_broadcast)


class LikePostAPIView(generics.CreateAPIView, generics.DestroyAPIView):
    serializer_class = LikeSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        ClusterPostPermission,
    ]

    def get_object(self) -> Like:
        like = get_object_or_404(
            Like.objects.select_related(
                "post",
                "created_by",
            ).prefetch_related(
                "post__cluster",
                "post__created_by",
                "post__files",
                "post__files",
                "post__likes",
                "post__shares",
            ),
            post_id=self.kwargs["post_id"],
        )

        # NOTE: (Joseph) for now lets handle it this way
        # so only a user can delete their post
        if (like.created_by_id != self.request.user.id) and (
            self.request.method.upper() == "DELETE"
        ):
            self.permission_denied(request=self.request)

        self.check_object_permissions(request=self.request, obj=like.post.cluster)
        return like

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        self.post_object = get_object_or_404(
            Post.objects.prefetch_related("cluster", "created_by", "files"),
            id=self.kwargs["post_id"],
            cluster_id=self.kwargs["cluster_id"],
        )
        self.check_object_permissions(
            request=self.request, obj=self.post_object.cluster
        )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer: LikeSerializer) -> None:
        serializer.save(created_by=self.request.user, post_id=self.kwargs["post_id"])

        # broadcast event to cluster and post channels
        channels = [
            self.post_object.channel_name,
            self.post_object.cluster.channel_name,
        ]
        CentrifugoConnector().broadcast_event(
            event_name=CENT_EVENT_POST_LIKE_CREATED,
            channels=channels,
            event_data=dict(
                PostSerializer(context={"request": self.request}).to_representation(
                    instance=self.post_object
                )
            ),
        )

    def perform_destroy(self, instance: Like) -> None:
        post = instance.post
        super().perform_destroy(instance)
        post.refresh_from_db()

        # broadcast event to cluster and post channels
        channels = [post.channel_name, post.cluster.channel_name]
        CentrifugoConnector().broadcast_event(
            event_name=CENT_EVENT_POST_LIKE_DELETED,
            channels=channels,
            event_data=dict(
                PostSerializer(context={"request": self.request}).to_representation(
                    instance=post
                )
            ),
        )


class CommentListAPIView(generics.ListCreateAPIView):
    """List/create comments on a post."""

    serializer_class = CommentSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        ClusterPostPermission,
    ]

    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["content"]
    ordering_fields = ["created_datetime"]
    ordering = ["-created_datetime"]

    def get_object(self) -> Cluster:
        cluster = get_object_or_404(Cluster, id=self.kwargs["cluster_id"])
        self.check_object_permissions(request=self.request, obj=cluster)
        return cluster

    def get_queryset(self) -> QuerySet:
        cluster = self.get_object()
        return Comment.objects.filter(
            post__cluster=cluster,
            post__id=self.kwargs["post_id"],
            replying__isnull=True,
        )

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        self.get_object()
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer) -> None:
        serializer.save(
            created_by=self.request.user,
            post_id=self.kwargs["post_id"],
        )


class RepliesListAPIView(generics.ListCreateAPIView):
    """List/create replies to a comment."""

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, ClusterPostPermission]

    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["content"]
    ordering_fields = ["created_datetime"]
    ordering = ["-created_datetime"]

    def get_object(self) -> Cluster:
        cluster = get_object_or_404(
            Cluster,
            id=self.kwargs["cluster_id"],
        )
        self.check_object_permissions(request=self.request, obj=cluster)
        return cluster

    def get_queryset(self) -> QuerySet:
        cluster = self.get_object()

        return Comment.objects.filter(
            post__cluster=cluster,
            post__id=self.kwargs["post_id"],
            replying__id=self.kwargs["comment_id"],
        )

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        self.get_object()
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer) -> None:
        serializer.save(
            created_by=self.request.user,
            post_id=self.kwargs["post_id"],
            replying_id=self.kwargs["comment_id"],
        )


class FileUploadAPIView(generics.CreateAPIView):
    """Upload media file."""

    serializer_class = FileModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    @extend_schema(
        operation_id="upload_file",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                    "file_type": {"type": "integer", "format": "string"},
                },
            }
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer) -> None:
        serializer.save(created_by=self.request.user)


class DMCreateAPIView(generics.CreateAPIView):
    """Create DM."""

    serializer_class = CreateDMSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer: CreateDMSerializer) -> None:
        dm = serializer.save(created_by=self.request.user)

        # send dm creation event to centrifugo
        channels = [user.channel_name for user in dm.friendship.users.all()]
        CentrifugoConnector().broadcast_event(
            event_name=CENT_EVENT_DM_CREATED,
            channels=channels,
            event_data=serializer.data,
        )


class ListDMAPIView(generics.ListAPIView):
    """List DMs."""

    serializer_class = UpdateDMSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ["created_datetime"]
    search_fields = ["content"]
    ordering = ["-created_datetime"]

    def get_queryset(self) -> QuerySet[DM]:
        return DM.objects.prefetch_related("created_by", "friendship", "files").filter(
            friendship_id=self.kwargs["friendship_id"],
            friendship__users__id=self.request.user.id,
        )


class RetrieveUpdateDMAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve update or delete DM."""

    serializer_class = UpdateDMSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "put", "delete"]

    def get_object(self) -> DM:
        query = {
            "id": self.kwargs["message_id"],
            "friendship_id": self.kwargs["friendship_id"],
            "friendship__users__id": self.request.user.id,
        }

        # ensure that only dm creator can delete or update dm.
        if self.request.method.upper() in ["DELETE", "PUT"]:
            query["created_by"] = self.request.user

        return get_object_or_404(
            DM.objects.prefetch_related("created_by", "friendship", "files"), **query
        )

    def perform_update(self, serializer: UpdateDMSerializer) -> None:
        dm = serializer.save(edited=True)
        # send dm creation event to centrifugo
        channels = [user.channel_name for user in dm.friendship.users.all()]
        CentrifugoConnector().broadcast_event(
            event_name=CENT_EVENT_DM_EDITED,
            channels=channels,
            event_data=serializer.data,
        )

    def perform_destroy(self, instance: DM) -> None:
        channels = [user.channel_name for user in instance.friendship.users.all()]
        data_to_broadcast = {
            "event_name": CENT_EVENT_DM_EDITED,
            "channels": channels,
            "event_data": dict(
                UpdateDMSerializer(instance=instance).to_representation(
                    instance=instance
                )
            ),
        }

        super().perform_destroy(instance)

        # send dm deletion event to centrifugo
        CentrifugoConnector().broadcast_event(**data_to_broadcast)
