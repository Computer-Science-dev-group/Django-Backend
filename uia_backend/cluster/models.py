from datetime import timedelta

from django.db import models
from instant.models import Channel

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
    channel = models.OneToOneField(Channel, on_delete=models.CASCADE)
    created_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT, null=True)

    class Meta:
        permissions = CLUSTER_PERMISSIONS


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


class ClusterEvent(BaseAbstractModel):
    EVENT_TYPE_PHYSICAL = 0
    EVENT_TYPE_VIRTUAL = 1
    EVENT_TYPE_HYBRID = 2

    EVENT_STATUS_AWAITING = 0
    EVENT_STATUS_ONGOING = 1
    EVENT_STATUS_CANCELLED = 2
    EVENT_STATUS_EXPIRED = 3

    EVENT_TYPES = (
        (EVENT_TYPE_PHYSICAL, "Physical"),
        (EVENT_TYPE_VIRTUAL, "Virtual"),
        (EVENT_TYPE_HYBRID, "Hybrid"),
    )

    STATUS_CHOICES = (
        (EVENT_STATUS_AWAITING, "Awaiting"),
        (EVENT_STATUS_ONGOING, "Ongoing"),
        (EVENT_STATUS_CANCELLED, "Cancelled"),
        (EVENT_STATUS_EXPIRED, "Expired"),
    )

    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    location = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=EVENT_STATUS_AWAITING
    )
    link = models.URLField(blank=True, null=True)
    attendees = models.ManyToManyField(
        CustomUser,
        through="EventAttendance",
        through_fields=["event", "attendee"],
        related_name="attended_events",
    )
    created_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT, null=True)
    event_date = models.DateTimeField()

    def cancel(self):
        self.status = ClusterEvent.EVENT_STATUS_CANCELLED
        self.save()
        # Notify attendees about event cancellation

    def save(self, *args, **kwargs):
        # Checks if the User object has not been created
        if ClusterEvent.objects.filter(pk=self.pk).exists() is False:
            cluster_membership = ClusterMembership.objects.filter(
                user=self.created_by, cluster=self.cluster
            ).first()
            if not cluster_membership:
                raise Exception("User is not a member of the cluster.")
        super().save(*args, **kwargs)


class EventAttendance(BaseAbstractModel):
    EVENT_ATTENDANCE_STATUS_INVITED = 0
    EVENT_ATTENDANCE_STATUS_ATTENDING = 1
    EVENT_ATTENDANCE_STATUS_NOT_ATTENDING = 2
    EVENT_ATTENDANCE_STATUS_CHOICES = (
        (EVENT_ATTENDANCE_STATUS_INVITED, "Invited"),
        (EVENT_ATTENDANCE_STATUS_ATTENDING, "Attending"),
        (EVENT_ATTENDANCE_STATUS_NOT_ATTENDING, "Not Attending"),
    )

    event = models.ForeignKey(ClusterEvent, on_delete=models.CASCADE)
    attendee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    status = models.PositiveSmallIntegerField(
        choices=EVENT_ATTENDANCE_STATUS_CHOICES, default=EVENT_ATTENDANCE_STATUS_INVITED
    )

    def mark_attending(self):
        self.status = EventAttendance.EVENT_ATTENDANCE_STATUS_ATTENDING
        self.save()

    def mark_not_attending(self):
        self.status = EventAttendance.EVENT_ATTENDANCE_STATUS_NOT_ATTENDING
        self.save()
