from uia_backend.cluster.constants import (
    ADD_CLUSTER_MEMBER_PERMISSION,
    REMOVE_CLUSTER_MEMBER_PERMISSION,
    UPDATE_CLUSTER_PERMISSION,
    VIEW_CLUSTER_PERMISSION,
)
from uia_backend.libs.permissions import CustomAccessPermission


class ClusterObjectPermission(CustomAccessPermission):
    perms_map = {
        "GET": [VIEW_CLUSTER_PERMISSION],
        "OPTIONS": [],
        "HEAD": [],
        "POST": [VIEW_CLUSTER_PERMISSION],
        "PUT": [VIEW_CLUSTER_PERMISSION, UPDATE_CLUSTER_PERMISSION],
        "PATCH": [VIEW_CLUSTER_PERMISSION, UPDATE_CLUSTER_PERMISSION],
    }


class ClusterInvitationObjectPermission(CustomAccessPermission):
    perms_map = {
        "GET": [VIEW_CLUSTER_PERMISSION],
        "OPTIONS": [],
        "HEAD": [],
        "POST": [VIEW_CLUSTER_PERMISSION, ADD_CLUSTER_MEMBER_PERMISSION],
        "PUT": [VIEW_CLUSTER_PERMISSION, ADD_CLUSTER_MEMBER_PERMISSION],
        "PATCH": [VIEW_CLUSTER_PERMISSION, ADD_CLUSTER_MEMBER_PERMISSION],
        "DELETE": [VIEW_CLUSTER_PERMISSION, ADD_CLUSTER_MEMBER_PERMISSION],
    }


class ClusterMembersObjectPermission(CustomAccessPermission):
    perms_map = {
        "GET": [VIEW_CLUSTER_PERMISSION],
        "OPTIONS": [],
        "HEAD": [],
        "DELETE": [VIEW_CLUSTER_PERMISSION, REMOVE_CLUSTER_MEMBER_PERMISSION],
    }


class InternalClusterProtectionPermission(CustomAccessPermission):
    """Permission to protect internal clusters."""

    perms_map = {
        "DELETE": ["PROTECT_INTERNAL_CLUSTERS"],
    }
