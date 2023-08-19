from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from encrypted_model_fields.fields import EncryptedTextField

from uia_backend.accounts.models import CustomUser, FriendShip
from uia_backend.cluster.models import Cluster
from uia_backend.libs.base_models import BaseAbstractModel


def file_upload_location(instance, filename: str) -> str:
    """Return file upload location."""

    date = timezone.now().date().isoformat()
    location = f"media/{date}/{filename}"

    if instance.created_by:
        location = f"users/{instance.created_by.id}/media/{filename}"

    return location


def validate_file_size(value: Any) -> Any:
    filesize = value.size

    if filesize > settings.MAX_MEDIA_UPLOAD_SIZE:
        raise ValidationError("File size has exceeded max file upload size (10MB)")
    else:
        return value


class FileModel(BaseAbstractModel):
    """Model represening an uploaded file."""

    FILE_TYPE_IMAGE = 0
    FILE_TYPE_VIDEO = 1
    FILE_TYPE_AUDIO = 2
    FILE_TYPE_DOCUMENT = 3
    FILE_TYPE_OTHER = 4

    FILE_TYPE_CHOICES = (
        (FILE_TYPE_IMAGE, "Image File"),
        (FILE_TYPE_VIDEO, "Video File"),
        (FILE_TYPE_AUDIO, "Audio File"),
        (FILE_TYPE_DOCUMENT, "Document File"),
        (FILE_TYPE_OTHER, "Uncategorized File"),
    )

    file_type = models.IntegerField(choices=FILE_TYPE_CHOICES, max_length=50)
    file = models.FileField(
        upload_to=file_upload_location, validators=[validate_file_size]
    )
    comment = models.ForeignKey(
        "messaging.Comment", on_delete=models.CASCADE, related_name="files", null=True
    )
    post = models.ForeignKey(
        "messaging.Post", on_delete=models.CASCADE, related_name="files", null=True
    )
    dm = models.ForeignKey(
        "messaging.DM", on_delete=models.CASCADE, related_name="files", null=True
    )

    created_by = models.ForeignKey(
        CustomUser,
        related_name="files",
        on_delete=models.PROTECT,
        null=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    (
                        Q(comment__isnull=True)
                        & Q(post__isnull=False)
                        & Q(dm__isnull=True)
                    )
                    | (
                        Q(comment__isnull=False)
                        & Q(post__isnull=True)
                        & Q(dm__isnull=True)
                    )
                    | (
                        Q(comment__isnull=True)
                        & Q(post__isnull=True)
                        & Q(dm__isnull=False)
                    )
                    | (
                        Q(comment__isnull=True)
                        & Q(post__isnull=True)
                        & Q(dm__isnull=True)
                    )
                ),
                name="%(app_label)s_%(class)s Must set one of comment, post, or dm.",
            )
        ]


class Post(BaseAbstractModel):
    """Model represening a post to a cluster."""

    title = models.TextField(max_length=300)
    content = models.TextField(max_length=2000)
    is_shared = models.BooleanField(default=False)
    cluster = models.ForeignKey(Cluster, related_name="posts", on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        CustomUser, related_name="posts", on_delete=models.PROTECT
    )

    @property
    def channel_name(self) -> str:
        """Return centrifugo channel_name."""
        return f"${settings.POST_NAMESPACE}:{self.id}"


class Comment(BaseAbstractModel):
    """Model representing a comment to a post or a reply to another comment."""

    content = models.TextField(max_length=2000)
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    replying = models.ForeignKey(
        "messaging.Comment", related_name="replies", on_delete=models.CASCADE, null=True
    )
    created_by = models.ForeignKey(
        CustomUser, related_name="comments", on_delete=models.PROTECT
    )


class Like(BaseAbstractModel):
    """Model representing the liking of a post."""

    post = models.ForeignKey(
        Post, related_name="likes", on_delete=models.CASCADE, null=True
    )
    comment = models.ForeignKey(
        Comment, related_name="likes", on_delete=models.CASCADE, null=True
    )
    created_by = models.ForeignKey(
        CustomUser, related_name="likes", on_delete=models.PROTECT
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(comment__isnull=True) & Q(post__isnull=False))
                    | (Q(comment__isnull=False) & Q(post__isnull=True))
                ),
                name="%(app_label)s_%(class)s Must set one and only one of comment or post.",
            )
        ]

    def __str__(self):
        return (
            f'User {self.created_by.email} liked {"Post" if self.post else "Comment" } '
            f"{self.post.id if self.post else self.comment.id}"
        )


class Share(BaseAbstractModel):
    """Model representing the sharing of a post."""

    comment = models.TextField(blank=True, max_length=300)
    shared_post = models.ForeignKey(
        Post, related_name="shares", on_delete=models.PROTECT
    )
    new_post = models.OneToOneField(
        Post, related_name="shared_from", on_delete=models.PROTECT
    )
    cluster = models.ForeignKey(Cluster, on_delete=models.PROTECT)
    created_by = models.ForeignKey(
        CustomUser, related_name="shares", on_delete=models.PROTECT
    )

    def __str__(self):
        return f"User {self.created_by.email} shared post {self.shared_post.id}"


class DM(BaseAbstractModel):
    """Model representing a direct message between two users."""

    content = EncryptedTextField(blank=True, max_length=1000, default="")
    friendship = models.ForeignKey(FriendShip, on_delete=models.CASCADE)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    replying = models.ForeignKey(
        "messaging.DM", related_name="replies", on_delete=models.CASCADE, null=True
    )
    edited = models.BooleanField(default=False)
