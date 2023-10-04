from typing import Any

from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response

from uia_backend.cluster.api.v1.permissions import (
    ClusterInvitationObjectPermission,
    ClusterMembersObjectPermission,
    ClusterObjectPermission,
    InternalClusterProtectionPermission,
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
from uia_backend.notification import constants as notification_constants
from uia_backend.notification.utils.notification_senders import Notifier


class ClusterListCreateAPIView(generics.ListCreateAPIView):
    """List/Create clusters API View."""

    serializer_class = ClusterSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["title", "created_datetime"]
    ordering = ["-created_datetime"]

    def get_queryset(self) -> QuerySet:
        """Get users clusters."""
        return Cluster.objects.select_related("internal_cluster").filter(
            members__id=self.request.user.id,
        )

   
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
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["created_datetime"]
    search_fields = [
        "user__first_name",
        "user__last_name",
    ]
    ordering_fields = ["created_datetime", "user__first_name", "user__last_name"]
    ordering = ["-created_datetime"]

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
    permission_classes = [
        permissions.IsAuthenticated,
        ClusterMembersObjectPermission,
    ]

    def get_object(self) -> ClusterMembership:
        membership_record = get_object_or_404(
            ClusterMembership.objects.select_related("cluster"),
            cluster_id=self.kwargs["cluster_id"],
            id=self.kwargs["membership_id"],
        )

        # if its an internal cluster apply the InternalClusterProtectionPermission
        # NOTE: This is a crud fix to ensure users can not leave internal clusters
        if membership_record.cluster.internal_cluster is not None:
            self.permission_classes = (
                permissions.IsAuthenticated,
                InternalClusterProtectionPermission,
            )
            self.check_object_permissions(
                request=self.request, obj=membership_record.cluster
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
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "created_by"]
    search_fields = ["user__first_name", "user__last_name"]
    ordering_fields = [
        "status",
        "created_datetime",
        "user__first_name",
        "user__last_name",
    ]
    ordering = ["-created_datetime"]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # ensure object permission check runs
        self.get_object()
        return super().post(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[ClusterInvitation]:
        cluster = self.get_object()
        return super().get_queryset().filter(cluster=cluster)

    def get_object(self) -> Cluster:
        cluster = get_object_or_404(
            self.request.user.cluster_member_set, id=self.kwargs["cluster_id"]
        )
        self.check_object_permissions(request=self.request, obj=cluster)
        return cluster

    def perform_create(self, serializer: ClusterInvitationSerializer) -> None:
        notification = serializer.save(
            created_by=self.request.user,
            cluster_id=self.kwargs["cluster_id"],
        )

        # send in app notification to invlitation recipient
        notification_data = {
            "recipients": [notification.user],
            "verb": "invited you to a cluster",
            "actor": notification.created_by,
            "target": notification.cluster,
            "metadata": dict(serializer.to_representation(notification)),
        }
        notifier = Notifier(
            event=notification_constants.NOTIFICATION_TYPE_RECIEVED_CLUSTER_INVITATION, data=notification_data
        )

        notifier.send_notification()


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
    
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        invitation_record = ClusterInvitation.objects.get(id=self.kwargs["invitation_id"])

        notification_data = {
            "recipients": [invitation_record.user],
            "verb":  "Cancelled your invitation to cluster",
            "actor": invitation_record.created_by,
            "target": invitation_record.cluster,
            "metadata": None
        }
        notifier = Notifier(
                event=notification_constants.NOTIFICATION_TYPE_CANCELED_CLUSTER_INVITATION,
                data=notification_data,
        )
        notifier.send_notification()

        return super().patch(request, *args, **kwargs)

        

class UserClusterInvitationListAPIView(generics.ListAPIView):
    serializer_class = ClusterInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["cluster__title"]
    ordering_fields = ["status", "created_datetime"]
    ordering = ["-created_datetime"]

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
    
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:

        invitation_record = ClusterInvitation.objects.get(id=self.kwargs["invitation_id"])
        status = self.request.data["status"]

        notification_data = {
            "recipients": [invitation_record.created_by],
            "verb": "Accepted invitation to cluster" if status == ClusterInvitation.INVITATION_STATUS_ACCEPTED else "rejected invitation to cluster",
            "actor": invitation_record.user,
            "target": invitation_record.cluster,
            "metadata": None
        }
        notifier = Notifier(
                event=notification_constants.NOTIFICATION_TYPE_ACCEPT_CLUSTER_INVITATION if status == ClusterInvitation.INVITATION_STATUS_ACCEPTED else notification_constants.NOTIFICATION_TYPE_REJECT_CLUSTER_INVITATION,
                data=notification_data,
        )
        notifier.send_notification()

        return super().patch(request, *args, **kwargs)