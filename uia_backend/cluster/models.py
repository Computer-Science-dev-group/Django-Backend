from datetime import timedelta

from django.conf import settings
from django.db import models

from uia_backend.accounts.models import CustomUser
from uia_backend.cluster.constants import CLUSTER_PERMISSIONS
from uia_backend.libs.base_models import BaseAbstractModel


class InternalCluster(BaseAbstractModel):
    """Model representing an internal Cluster."""

    name = models.CharField(max_length=100, db_index=True, unique=True, editable=False)
    description = models.TextField(default="")
    is_active = models.BooleanField(default=True)


def cluster_icon_upload_location(instance, filename: str) -> str:
    """Get Location for user profile photo upload."""
    return f"clusters/{instance.id}/icon/{filename}"


class Cluster(BaseAbstractModel):
    internal_cluster = models.OneToOneField(
        InternalCluster, null=True, db_index=True, on_delete=models.PROTECT
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to=cluster_icon_upload_location, null=True)
    members = models.ManyToManyField(
        CustomUser,
        through="cluster.ClusterMembership",
        through_fields=["cluster", "user"],
        related_name="cluster_member_set",
    )
    created_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT, null=True)

    class Meta:
        permissions = CLUSTER_PERMISSIONS

    @property
    def channel_name(self):
        """Return centrifugo channel name for model."""
        channel_name = (
            f"{settings.PUBLIC_CLUSTER_NAMESPACE}:{self.id}"
            if self.internal_cluster
            else f"{settings.PRIVATE_CLUSTER_NAMESPACE}:{self.id}"
        )
        return channel_name


class ClusterInvitation(BaseAbstractModel):
    INVITATION_STATUS_PENDING = 0
    INVITATION_STATUS_ACCEPTED = 1
    INVITATION_STATUS_REJECTED = 2
    INVITATION_STATUS_EXPIRED = 3
    INVITATION_STATUS_CANCLED = 4

    INVITATION_STATUS_CHOICES = (
        (INVITATION_STATUS_PENDING, "Pending"),
        (INVITATION_STATUS_ACCEPTED, "Accepted"),
        (INVITATION_STATUS_REJECTED, "Rejected"),
        (INVITATION_STATUS_EXPIRED, "Expired"),
        (INVITATION_STATUS_CANCLED, "Cancled"),
    )

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="cluster_invitations"
    )
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    status = models.IntegerField(
        choices=INVITATION_STATUS_CHOICES, default=INVITATION_STATUS_PENDING
    )
    duration = models.DurationField(
        help_text="Duration in days.",
        default=timedelta(days=1),
    )
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT, related_name="cluster_invitation_set"
    )


class ClusterMembership(BaseAbstractModel):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    invitation = models.ForeignKey(
        ClusterInvitation, on_delete=models.CASCADE, null=True
    )
