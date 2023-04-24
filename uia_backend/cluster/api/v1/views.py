from typing import Any

from django.db import transaction
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response

from uia_backend.cluster.api.v1.permissions import (
    ClusterInvitationObjectPermission,
    ClusterMembersObjectPermission,
    ClusterObjectPermission,
)
from uia_backend.cluster.api.v1.serializers import (
    ClusterInvitationSerializer,
    ClusterMembershipSerializer,
    ClusterSerializer,
)
from uia_backend.cluster.constants import (
    ADD_CLUSTER_MEMBER_PERMISSION,
    REMOVE_CLUSTER_MEMBER_PERMISSION,
    UPDATE_CLUSTER_PERMISSION,
    VIEW_CLUSTER_PERMISSION,
)
from uia_backend.cluster.models import Cluster, ClusterInvitation, ClusterMembership
from uia_backend.libs.permissions import unassign_object_permissions


class ClusterListCreateAPIView(generics.ListCreateAPIView):
    """List/Create clusters API View."""

    serializer_class = ClusterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        """Get users clusters."""
        return self.request.user.cluster_member_set.all()

    def perform_create(self, serializer: ClusterSerializer) -> None:
        serializer.save(created_by=self.request.user)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    @transaction.atomic()
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().post(request, *args, **kwargs)


class ClusterDetailAPIView(generics.RetrieveUpdateAPIView):
    """Retrieve/Update a cluster API View."""

    serializer_class = ClusterSerializer
    permission_classes = [permissions.IsAuthenticated, ClusterObjectPermission]

    def get_object(self) -> Cluster:
        cluster = get_object_or_404(
            self.request.user.cluster_member_set, id=self.kwargs["cluster_id"]
        )
        self.check_object_permissions(request=self.request, obj=cluster)
        return cluster


class ClusterMembershipListAPIView(generics.ListAPIView):
    serializer_class = ClusterMembershipSerializer
    permission_classes = [permissions.IsAuthenticated, ClusterMembersObjectPermission]
    queryset = ClusterMembership.objects.all()

    def get_queryset(self) -> QuerySet:
        # Apply cluster permissions
        cluster = self.get_object()
        return super().get_queryset().filter(cluster=cluster)

    def get_object(self) -> Any:
        cluster = get_object_or_404(
            self.request.user.cluster_member_set, id=self.kwargs["cluster_id"]
        )
        self.check_object_permissions(request=self.request, obj=cluster)
        return cluster


class ClusterMembersDetailAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = ClusterMembershipSerializer
    permission_classes = [permissions.IsAuthenticated, ClusterMembersObjectPermission]

    def get_object(self) -> ClusterMembership:
        membership_record = get_object_or_404(
            ClusterMembership.objects.select_related("cluster"),
            cluster_id=self.kwargs["cluster_id"],
            id=self.kwargs["membership_id"],
        )

        if membership_record.user == self.request.user:
            # we want to ensure that user can delete their own membership data
            return membership_record

        self.check_object_permissions(
            request=self.request, obj=membership_record.cluster
        )
        return membership_record

    def perform_destroy(self, instance: ClusterMembership) -> None:
        # remove all cluster permissions from member before deleting
        unassign_object_permissions(
            permissions=[
                VIEW_CLUSTER_PERMISSION,
                UPDATE_CLUSTER_PERMISSION,
                ADD_CLUSTER_MEMBER_PERMISSION,
                REMOVE_CLUSTER_MEMBER_PERMISSION,
            ],
            assignee=instance.user,
            obj=instance.cluster,
        )
        instance.delete()


class ClusterInvitationListAPIView(generics.ListCreateAPIView):
    """List/Create Cluster Invitation API View."""

    serializer_class = ClusterInvitationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        ClusterInvitationObjectPermission,
    ]
    queryset = ClusterInvitation.objects.all()

    def get_queryset(self) -> QuerySet[ClusterInvitation]:
        cluster = self.get_object()
        return super().get_queryset().filter(cluster=cluster)

    def get_object(self) -> Cluster:
        cluster = get_object_or_404(
            self.request.user.cluster_member_set, id=self.kwargs["cluster_id"]
        )
        self.check_object_permissions(request=self.request, obj=cluster)
        return cluster

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # ensure object permission check runs
        self.get_object()
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer: ClusterInvitationSerializer) -> None:
        serializer.save(
            created_by=self.request.user,
            cluster_id=self.kwargs["cluster_id"],
        )


class ClusterInvitationDetailAPIView(generics.RetrieveUpdateAPIView):
    """Retrieve/Update a Cluster Invitation API View."""

    serializer_class = ClusterInvitationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        ClusterInvitationObjectPermission,
    ]
    http_method_names = ["get", "patch"]

    def get_object(self) -> ClusterInvitation:
        invitation_record = get_object_or_404(
            ClusterInvitation.objects.select_related("cluster"),
            cluster_id=self.kwargs["cluster_id"],
            id=self.kwargs["invitation_id"],
        )

        self.check_object_permissions(
            request=self.request, obj=invitation_record.cluster
        )
        return invitation_record


class UserClusterInvitationListAPIView(generics.ListAPIView):
    serializer_class = ClusterInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return self.request.user.cluster_invitations.all()


class UserClusterInvitationDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ClusterInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch"]

    def get_object(self):
        return get_object_or_404(
            self.request.user.cluster_invitations, id=self.kwargs["invitation_id"]
        )
