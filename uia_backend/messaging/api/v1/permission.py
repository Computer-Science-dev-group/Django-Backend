from uia_backend.cluster.constants import VIEW_CLUSTER_PERMISSION
from uia_backend.libs.permissions import CustomAccessPermission


class ClusterPostPermission(CustomAccessPermission):
    perms_map = {
        "OPTIONS": [],
        "HEAD": [],
        "GET": [VIEW_CLUSTER_PERMISSION],
        "POST": [VIEW_CLUSTER_PERMISSION],
        "DELETE": [],
    }
