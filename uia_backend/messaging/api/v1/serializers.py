from typing import Any

from django.conf import settings
from django.core.files import File
from django.db.models import QuerySet
from rest_framework import serializers

from uia_backend.accounts.api.v1.serializers import ProfileSerializer
from uia_backend.libs.serializers import DynamicFieldsModelSerializer
from uia_backend.messaging.models import Comment, FileModel, Like, Post


class FileModelSerializer(DynamicFieldsModelSerializer[FileModel]):
    post = serializers.PrimaryKeyRelatedField(read_only=True)
    comment = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = FileModel
        fields = [
            "id",
            "file_type",
            "file",
            "created_by",
            "post",
            "comment",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "post",
            "comment",
        ]

    def validate_file(self, value: File) -> File:
        if value.size > settings.MAX_MEDIA_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f"File size has exceeded max file upload size {settings.MAX_MEDIA_UPLOAD_SIZE / (1024 ** 2)}MB"
            )
        return value


class PostSerializer(serializers.ModelSerializer[Post]):
    shares = serializers.IntegerField(read_only=True, default=0, source="shares__count")
    likes = serializers.IntegerField(read_only=True, default=0, source="likes_count")
    comments = serializers.IntegerField(
        read_only=True,
        default=0,
        source="comments__count",
    )
    liked_by_user = serializers.BooleanField(default=False, read_only=True)
    share_comment = serializers.CharField(
        required=False,
        read_only=True,
        source="shared_from__comment",
        default=None,
    )

    created_by = ProfileSerializer(read_only=True)

    file_ids = serializers.PrimaryKeyRelatedField(
        source="files",
        many=True,
        queryset=FileModel.objects.filter(
            post__isnull=True,
            comment__isnull=True,
        ),
        write_only=True,
    )

    files = FileModelSerializer(read_only=True, many=True, allowed_fields=["file"])
    ws_channel_name = serializers.CharField(read_only=True, source="channel_name")

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "content",
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
            "file_ids",
            "ws_channel_name",
        ]

        read_only_fields = [
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

    def validate_file_ids(self, value: list[FileModel]) -> QuerySet:
        """Validate files_ids"""
        user = self.context["request"].user

        for file in value:
            if file.created_by != user:
                raise serializers.ValidationError("Invaid file id.")

        return value

    def to_representation(self, instance: Post) -> dict[str, Any]:
        """Return dict representaion of serializer."""
        user = self.context["request"].user
        data = super().to_representation(instance)
        data["likes"] = instance.likes.count()
        data["shares"] = instance.shares.count()
        data["comments"] = instance.comments.filter(replying__isnull=True).count()
        data["liked_by_user"] = instance.likes.filter(created_by=user).exists()
        return data


class CommentSerializer(serializers.ModelSerializer[Comment]):
    replies = serializers.IntegerField(
        default=0, read_only=True, source="replies_count"
    )
    likes = serializers.IntegerField(default=0, read_only=True, source="likes_count")
    created_by = ProfileSerializer(read_only=True)
    liked_by_user = serializers.BooleanField(default=False, read_only=True)
    cluster = serializers.UUIDField(source="post__cluster", read_only=True)

    file_ids = serializers.PrimaryKeyRelatedField(
        source="files",
        many=True,
        queryset=FileModel.objects.filter(
            post__isnull=True,
            comment__isnull=True,
        ),
        write_only=True,
    )

    files = FileModelSerializer(read_only=True, many=True, allowed_fields=["file"])

    class Meta:
        model = Comment
        fields = [
            "id",
            "post",
            "cluster",
            "replying",
            "created_by",
            "created_datetime",
            "likes",
            "replies",
            "liked_by_user",
            "content",
            "file_ids",
            "files",
        ]

        read_only_fields = [
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

    def validate_file_ids(self, value: list[FileModel]) -> QuerySet:
        """Validate files_ids"""
        user = self.context["request"].user

        for file in value:
            if file.created_by != user:
                raise serializers.ValidationError("Invaid file id.")

        return value

    def to_representation(self, instance: Comment) -> dict[str, Any]:
        """Return dict representaion of serializer."""
        user = self.context["request"].user
        data = super().to_representation(instance)
        data["likes"] = instance.likes.all().count()
        data["replies"] = instance.replies.all().count()
        data["liked_by_user"] = instance.likes.filter(created_by=user).exists()
        return data


class LikeSerializer(serializers.ModelSerializer[Like]):
    created_by = ProfileSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ["id", "created_by", "created_datetime"]
        read_only_fields = ["id", "created_by", "created_datetime"]

    def create(self, validated_data: dict[str, Any]) -> Like:
        like, _ = Like.objects.get_or_create(**validated_data)
        return like
