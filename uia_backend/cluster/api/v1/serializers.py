import logging
import uuid
from datetime import timedelta
from typing import Any

from django.conf import settings
from instant.models import Channel
from rest_framework import serializers

from uia_backend.accounts.api.v1.serializers import UserProfileSerializer
from uia_backend.accounts.models import CustomUser
from uia_backend.cluster.constants import (
    ADD_CLUSTER_MEMBER_PERMISSION,
    REMOVE_CLUSTER_MEMBER_PERMISSION,
    UPDATE_CLUSTER_PERMISSION,
    VIEW_CLUSTER_PERMISSION,
)
from uia_backend.cluster.models import (
    Cluster,
    ClusterEvent,
    ClusterInvitation,
    ClusterMembership,
    EventAttendance,
)
from uia_backend.cluster.utils import send_event_creation_notification_mail
from uia_backend.libs.permissions import assign_object_permissions

logger = logging.getLogger()


class ClusterSerializer(serializers.ModelSerializer):
    is_default = serializers.BooleanField(
        source="internal_cluster__isnull", read_only=True
    )

    class Meta:
        model = Cluster
        fields = ["id", "title", "description", "icon", "created_by", "is_default"]
        read_only_fields = ["id", "created_by", "is_default"]

    def create(self, validated_data: dict[str, Any]) -> Cluster:
        """Create a cluster."""
        cluster_id = uuid.uuid4()
        channel = Channel.objects.create(
            name=f"{settings.PRIVATE_CLUSTER_NAMESPACE}:{cluster_id}",
            level=Channel.Level.Users,
        )
        validated_data["channel"] = channel
        validated_data["id"] = cluster_id
        cluster = super().create(validated_data)

        # we need to add the cluster creatot to the list of cluster members
        ClusterMembership.objects.create(
            cluster=cluster,
            user=cluster.created_by,
            invitation=None,
        )

        # assign all cluster permission to the creator
        creator_permissions = [
            VIEW_CLUSTER_PERMISSION,
            UPDATE_CLUSTER_PERMISSION,
            ADD_CLUSTER_MEMBER_PERMISSION,
            REMOVE_CLUSTER_MEMBER_PERMISSION,
        ]
        assign_object_permissions(
            permissions=creator_permissions,
            assignee=cluster.created_by,
            obj=cluster,
        )

        return cluster

    def to_representation(self, instance: Cluster) -> dict[str, Any]:
        """Construct serializer data."""
        data = dict(super().to_representation(instance))
        data["is_default"] = bool(instance.internal_cluster)
        return data


class ClusterInvitationSerializer(serializers.ModelSerializer):
    duration = serializers.IntegerField(
        min_value=1,
        max_value=10,
        required=True,
        source="duration.days",
    )

    class Meta:
        model = ClusterInvitation
        fields = ["id", "cluster", "status", "duration", "created_by", "user"]
        read_only_fields = ["id", "created_by", "cluster"]

    def validate_user(self, value: CustomUser) -> CustomUser:
        user = self.context["request"].user

        if user == value:
            raise serializers.ValidationError(
                "Invalid user. Can not send inivitation to this user."
            )

        return value

    def validate_status(self, value: int) -> int:
        """Validate value of status."""
        instance: ClusterInvitation | None = self.instance
        user = self.context["request"].user
        return_status = ClusterInvitation.INVITATION_STATUS_PENDING

        if instance and instance.status == ClusterInvitation.INVITATION_STATUS_PENDING:
            if user == instance.user and value in [
                ClusterInvitation.INVITATION_STATUS_ACCEPTED,
                ClusterInvitation.INVITATION_STATUS_REJECTED,
            ]:
                return_status = value
            elif (
                user != instance.user
                and value == ClusterInvitation.INVITATION_STATUS_CANCLED
            ):
                return_status = value

        return return_status

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if "duration" in attrs.keys():
            # NOTE: Joseph: Na beans if you know you know
            # Had to use this to cast duration.days to duration during validation
            attrs["duration"] = timedelta(days=attrs["duration"]["days"])

        return super().validate(attrs)

    def update(
        self, instance: ClusterInvitation, validated_data: dict[str, Any]
    ) -> ClusterInvitation:
        """Update cluster invitation."""
        # we want to ensure only invitation status can be updated
        validated_data.pop("user", None)
        return super().update(instance, validated_data)


class ClusterMembershipSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = ClusterMembership
        fields = ["id", "user"]
        read_only_fields = fields

    def update(
        self, instance: ClusterInvitation, validated_data: dict[str, Any]
    ) -> ClusterInvitation:
        """Overide method."""

    def create(self, validated_data: dict[str, Any]) -> ClusterInvitation:
        """Overide method."""


class EventAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventAttendance
        fields = ["id", "event", "attendee", "status"]
        read_only_fields = ("event", "attendee", "status")

    def rsvp_event(self, user):
        event_attendance = self.instance

        if event_attendance.status == EventAttendance.EVENT_ATTENDANCE_STATUS_ATTENDING:
            raise serializers.ValidationError("You have already RSVP'd for this event.")

        event_attendance.mark_attending()

        return event_attendance

    def cancel_event(self):
        event_attendance = self.instance

        if (
            event_attendance.status
            == EventAttendance.EVENT_ATTENDANCE_STATUS_NOT_ATTENDING
        ):
            raise serializers.ValidationError(
                "You have already canceled your RSVP for this event."
            )

        event_attendance.mark_not_attending()

        return event_attendance


class ClusterEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClusterEvent
        fields = [
            "id",
            "cluster",
            "title",
            "description",
            "event_type",
            "location",
            "link",
            "status",
            "attendees",
            "created_by",
            "event_date",
        ]
        read_only_fields = ("created_by", "cluster", "attendees")

    def validate(self, data):
        # Check if the user is a member of the event's cluster
        user = self.context["request"].user
        cluster = self.context.get("cluster")
        cluster_membership = ClusterMembership.objects.filter(
            user=user, cluster=cluster
        ).first()
        if not cluster_membership:
            raise serializers.ValidationError("User is not a member of the cluster.")

        return data

    def create(self, validated_data):
        # Automatically invite all members of the cluster
        cluster = validated_data["cluster"]
        attendees = cluster.members.all()
        event = ClusterEvent.objects.create(**validated_data)

        # Bulk create EventAttendance instances for all attendees in the cluster

        event_attendances = [
            EventAttendance(event=event, attendee=attendee) for attendee in attendees
        ]
        EventAttendance.objects.bulk_create(event_attendances)

        # Set the creator's EventAttendance status to 'attending'
        creator = self.context["request"].user
        creator_attendance = EventAttendance.objects.get(event=event, attendee=creator)
        creator_attendance.status = EventAttendance.EVENT_ATTENDANCE_STATUS_ATTENDING
        creator_attendance.save()
        # NOTE: I will include notification to the user about the RSVP here.
        send_event_creation_notification_mail(event)
        return event
