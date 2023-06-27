import logging
from typing import Any

from rest_framework import serializers

from uia_backend.accounts.api.v1.serializers import UserProfileSerializer
from uia_backend.accounts.models import CustomUser
from uia_backend.cluster.constants import (
    ADD_CLUSTER_MEMBER_PERMISSION,
    REMOVE_CLUSTER_MEMBER_PERMISSION,
    UPDATE_CLUSTER_PERMISSION,
    VIEW_CLUSTER_PERMISSION,
)
from uia_backend.cluster.models import Cluster, ClusterInvitation, ClusterMembership
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
    duration = serializers.IntegerField(min_value=1, max_value=10, required=True)

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
