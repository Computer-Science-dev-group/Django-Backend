from django.conf import settings
from django.db import transaction

from uia_backend.accounts.models import CustomUser
from uia_backend.cluster.constants import VIEW_CLUSTER_PERMISSION
from uia_backend.cluster.models import Cluster, ClusterMembership, InternalCluster
from uia_backend.libs.permissions import assign_object_permissions


class ClusterManager:

    """
    The ClusterManager class is responsible for managing the creation and membership of clusters for a given user.
    It adds a user to default clusters for the user based on their faculty, department, and year of graduation.
    """

    def __init__(self, user: CustomUser):
        """
        Initializes the ClusterManager object with a user and sets up the default
        cluster query and memberships to create.
        """
        self.user = user
        self.default_cluster_query = InternalCluster.objects.select_related(
            "cluster"
        ).filter(is_active=True)
        self.memberships_to_create: list[ClusterMembership] = []

    def _create_default_cluster(self, name: str, description: str) -> InternalCluster:
        """creates a default cluster with the given name and description."""

        internal_cluster, created = InternalCluster.objects.get_or_create(
            name=name, defaults={"description": description, "is_active": True}
        )

        if created or (getattr(internal_cluster, "cluster", None) is None):
            Cluster.objects.create(
                internal_cluster=internal_cluster,
                title=name.capitalize(),
            )

        return internal_cluster

    def _create_membership(self, cluster: Cluster) -> None:
        """Creates a membership for the user in the given cluster."""
        if not ClusterMembership.objects.filter(
            user=self.user, cluster=cluster
        ).exists():
            cluster = ClusterMembership(
                user=self.user, cluster=cluster, invitation=None
            )
            self.memberships_to_create.append(cluster)

    def _add_user_to_global_cluster(self) -> None:
        """Adds the user to the global default cluster."""
        global_cluster_name = settings.DEFUALT_CLUSTER_NAMES[0]

        try:
            global_cluster = self.default_cluster_query.get(name=global_cluster_name)
        except InternalCluster.DoesNotExist:
            global_cluster = self._create_default_cluster(
                name=global_cluster_name, description=""
            )
        self._create_membership(cluster=global_cluster.cluster)

    def _add_user_to_faculty_cluster(self) -> None:
        """Adds the user to the default cluster for their faculty."""
        faculty_cluster_name = str(settings.DEFUALT_CLUSTER_NAMES[1]).format(
            faculty_name=self.user.faculty
        )

        try:
            faculty_cluster = self.default_cluster_query.get(name=faculty_cluster_name)
        except InternalCluster.DoesNotExist:
            faculty_cluster = self._create_default_cluster(
                name=faculty_cluster_name, description=""
            )

        self._create_membership(cluster=faculty_cluster.cluster)

    def _add_user_to_department_cluster(self) -> None:
        """Adds the user to the default cluster for their department."""
        department_cluster_name = str(settings.DEFUALT_CLUSTER_NAMES[3]).format(
            department_name=self.user.department
        )
        try:
            department_cluster = self.default_cluster_query.get(
                name=department_cluster_name
            )
        except InternalCluster.DoesNotExist:
            department_cluster = self._create_default_cluster(
                name=department_cluster_name, description=""
            )

        self._create_membership(cluster=department_cluster.cluster)

    def _add_user_to_graduation_set_cluster(self) -> None:
        """Adds the user to the default cluster for their year of graduation."""
        graduation_set_cluster_name = str(settings.DEFUALT_CLUSTER_NAMES[4]).format(
            year_of_graduation=self.user.year_of_graduation
        )

        try:
            graduation_set_cluster_name = self.default_cluster_query.get(
                name=graduation_set_cluster_name
            )
        except InternalCluster.DoesNotExist:
            graduation_set_cluster_name = self._create_default_cluster(
                name=graduation_set_cluster_name, description=""
            )
        self._create_membership(cluster=graduation_set_cluster_name.cluster)

    @transaction.atomic()
    def add_user_to_defualt_clusters(self) -> None:
        """Adds the user to all default clusters."""
        self._add_user_to_global_cluster()
        self._add_user_to_faculty_cluster()
        self._add_user_to_department_cluster()
        self._add_user_to_graduation_set_cluster()

        memberships = ClusterMembership.objects.bulk_create(
            objs=self.memberships_to_create,
        )

        # assign membership permissions
        permissions = [VIEW_CLUSTER_PERMISSION]
        for record in memberships:
            assign_object_permissions(
                permissions=permissions, assignee=self.user, obj=record.cluster
            )
