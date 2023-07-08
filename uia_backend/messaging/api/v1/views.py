from typing import Any

from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, permissions
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from uia_backend.cluster.models import Cluster
from uia_backend.messaging.api.v1.permission import ClusterPostPermission
from uia_backend.messaging.api.v1.serializers import (
    CommentSerializer,
    FileModelSerializer,
    PostSerializer,
)
from uia_backend.messaging.models import Comment, Post


class PostListAPIView(generics.ListCreateAPIView):
    """List/create posts in a cluster."""

    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, ClusterPostPermission]

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_datetime"]
    ordering = ["-created_datetime"]

    def get_object(self) -> Cluster:
        cluster = get_object_or_404(Cluster, id=self.kwargs["cluster_id"])
        self.check_object_permissions(request=self.request, obj=cluster)
        return cluster

    def get_queryset(self) -> QuerySet[Post]:
        cluster = self.get_object()
        return Post.objects.filter(cluster=cluster)

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


class CommentListAPIView(generics.ListCreateAPIView):
    """List/create comments on a post."""

    serializer_class = CommentSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        ClusterPostPermission,
    ]

    filter_backends = [filters.OrderingFilter]
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

    filter_backends = [filters.OrderingFilter]
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
