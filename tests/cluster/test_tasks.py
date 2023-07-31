from datetime import datetime, timedelta

from django.test import TestCase
from freezegun import freeze_time

from tests.accounts.test_models import UserModelFactory
from tests.cluster.test_models import (
    ClusterChannelFactory,
    ClusterFactory,
    ClusterInvitationFactory,
)
from uia_backend.cluster.models import ClusterInvitation
from uia_backend.cluster.tasks import deactivate_expired_cluster_invitation


class DeactivateExpiredClusterInvitation(TestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        self.channel = ClusterChannelFactory()
        self.cluster = ClusterFactory.create(channel=self.channel)

    def test_method(self):
        """Test that only expired user invitation records are deactivated."""

        # SETUP

        # should not be marked as expired
        pending_records = ClusterInvitationFactory.create_batch(
            user=self.user,
            cluster=self.cluster,
            status=ClusterInvitation.INVITATION_STATUS_PENDING,
            duration=timedelta(days=4),
            size=3,
            created_by=self.user,
        )

        with freeze_time(lambda: datetime(2023, 6, 25)):
            # should be marked as expired
            expired_record = ClusterInvitationFactory.create_batch(
                user=self.user,
                cluster=self.cluster,
                status=ClusterInvitation.INVITATION_STATUS_PENDING,
                duration=timedelta(days=4),
                size=1,
                created_by=self.user,
            )

        # TESTS
        deactivate_expired_cluster_invitation()

        for record in pending_records:
            record.refresh_from_db()
            self.assertEqual(record.status, ClusterInvitation.INVITATION_STATUS_PENDING)

        for record in expired_record:
            record.refresh_from_db()
            self.assertEqual(record.status, ClusterInvitation.INVITATION_STATUS_EXPIRED)
