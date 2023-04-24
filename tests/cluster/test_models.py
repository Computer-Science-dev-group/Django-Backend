from factory.django import DjangoModelFactory

from uia_backend.cluster.models import (
    Cluster,
    ClusterInvitation,
    ClusterMembership,
    InternalCluster,
)


class InternalClusterFactory(DjangoModelFactory):
    name = "global"
    description = ""
    is_active = True

    class Meta:
        model = InternalCluster


class ClusterFactory(DjangoModelFactory):
    title = "My Cluster"
    description = ""

    class Meta:
        model = Cluster


class ClusterInvitationFactory(DjangoModelFactory):
    class Meta:
        model = ClusterInvitation


class ClusterMembershipFactory(DjangoModelFactory):
    class Meta:
        model = ClusterMembership
