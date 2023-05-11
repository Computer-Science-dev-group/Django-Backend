import random
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.utils import timezone

from tests.accounts.test_models import (
    EmailVerificationFactory,
    PasswordResetAttemptFactory,
    UserModelFactory,
)
from uia_backend.accounts.models import PasswordResetAttempt
from uia_backend.accounts.tasks import (
    change_status_of_expired_password_reset_records,
    deactivate_expired_email_verification_records,
)


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


class ChangeStatusOfExpiredPasswordResetRecords(TestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()

    def test_method(self):
        """Test that only expired password reset records are changed to expired status."""

        # SETUP
        expired_records = PasswordResetAttemptFactory.create_batch(
            user=self.user,
            status=random.choice(
                [
                    PasswordResetAttempt.STATUS_PENDING,
                    PasswordResetAttempt.STATUS_OTP_VERIFIED,
                ]
            ),
            expiration_datetime=timezone.now() - timedelta(hours=3),
            size=3,
        )

        already_expired_records = PasswordResetAttemptFactory.create_batch(
            status=PasswordResetAttempt.STATUS_EXPIRED,
            user=self.user,
            expiration_datetime=timezone.now() - timedelta(days=1),
            size=3,
        )

        active_records = PasswordResetAttemptFactory.create_batch(
            user=self.user,
            status=random.choice(
                [
                    PasswordResetAttempt.STATUS_PENDING,
                    PasswordResetAttempt.STATUS_OTP_VERIFIED,
                ]
            ),
            expiration_datetime=timezone.now() + timedelta(days=1),
            size=3,
        )

        # TESTS
        change_status_of_expired_password_reset_records()

        for record in expired_records:
            record.refresh_from_db()
            self.assertEqual(record.status, PasswordResetAttempt.STATUS_EXPIRED)

        for record in already_expired_records:
            record.refresh_from_db()
            self.assertEqual(record.status, PasswordResetAttempt.STATUS_EXPIRED)

        for record in active_records:
            record.refresh_from_db()
            self.assertNotEqual(record.status, PasswordResetAttempt.STATUS_EXPIRED)
