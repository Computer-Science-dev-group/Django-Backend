from django.urls import path

from uia_backend.cluster.api.v1.views import (
    ClusterDetailAPIView,
    ClusterInvitationDetailAPIView,
    ClusterInvitationListAPIView,
    ClusterListCreateAPIView,
    ClusterMembersDetailAPIView,
    ClusterMembershipListAPIView,
    UserClusterInvitationDetailAPIView,
    UserClusterInvitationListAPIView,
)

urlpatterns = [
    path("", ClusterListCreateAPIView.as_view(), name="list_create_cluster"),
    path(
        "<uuid:cluster_id>/",
        ClusterDetailAPIView.as_view(),
        name="retrieve_update_cluster",
    ),
    path(
        "<uuid:cluster_id>/members/",
        ClusterMembershipListAPIView.as_view(),
        name="list_cluster_members",
    ),
    path(
        "<uuid:cluster_id>/members/<uuid:membership_id>/",
        ClusterMembersDetailAPIView.as_view(),
        name="retrieve_delete_cluster_member",
    ),
    path(
        "<uuid:cluster_id>/invitations/",
        ClusterInvitationListAPIView.as_view(),
        name="list_create_cluster_invitation",
    ),
    path(
        "<uuid:cluster_id>/invitations/<uuid:invitation_id>/",
        ClusterInvitationDetailAPIView.as_view(),
        name="retrieve_update_cluster_invitation",
    ),
    path(
        "invitations/",
        UserClusterInvitationListAPIView.as_view(),
        name="list_users_cluster_invitation",
    ),
    path(
        "invitations/<uuid:invitation_id>/",
        UserClusterInvitationDetailAPIView.as_view(),
        name="retrieve_update_user_cluster_invitation",
    ),
]
