import uuid

import factory
from factory.django import DjangoModelFactory
from instant.models import Channel

from uia_backend.cluster.models import (
    Cluster,
    ClusterEvent,
    ClusterInvitation,
    ClusterMembership,
    EventAttendance,
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


class ClusterChannelFactory(DjangoModelFactory):
    name = factory.LazyAttribute(lambda obj: str(uuid.uuid4()))

    class Meta:
        model = Channel


class ClusterEventFactory(DjangoModelFactory):
    title = "Untitled Event"
    description = ""
    status = ClusterEvent.EVENT_STATUS_AWAITING
    event_type = ClusterEvent.EVENT_TYPE_PHYSICAL
    event_date = factory.Faker("future_datetime", end_date="+30d")

    class Meta:
        model = ClusterEvent


class EventAttendanceFactory(DjangoModelFactory):
    class Meta:
        model = EventAttendance
