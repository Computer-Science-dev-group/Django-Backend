from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.utils import timezone

from tests.accounts.test_models import EmailVerificationFactory, UserModelFactory
from uia_backend.accounts.tasks import deactivate_expired_email_verification_records


class DeactivateExpiredEmailVerificationRecords(TestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()

    def test_method(self):
        """Test that only expired email verification records are deactivated."""

        # SETUP
        expired_email_records = EmailVerificationFactory.create_batch(
            user=self.user,
            is_active=True,
            expiration_date=timezone.now() - relativedelta(hours=3),
            size=3,
        )

        already_deactivated_records = EmailVerificationFactory.create_batch(
            is_active=False,
            user=self.user,
            expiration_date=timezone.now() - relativedelta(days=1),
            size=3,
        )

        active_records = EmailVerificationFactory.create_batch(
            user=self.user,
            is_active=True,
            expiration_date=timezone.now() + relativedelta(days=1),
            size=3,
        )

        # TESTS
        deactivate_expired_email_verification_records()

        for record in expired_email_records:
            record.refresh_from_db()
            self.assertFalse(record.is_active)

        for record in already_deactivated_records:
            record.refresh_from_db()
            self.assertFalse(record.is_active)

        for record in active_records:
            record.refresh_from_db()
            self.assertTrue(record.is_active)
