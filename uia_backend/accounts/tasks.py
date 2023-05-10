from django.utils import timezone

from config.celery_app import app as CELERY_APP
from uia_backend.accounts.models import EmailVerification, PasswordResetAttempt


@CELERY_APP.task(name="deactivate_expired_email_verification_records")
def deactivate_expired_email_verification_records() -> None:
    """Deactivate email verification records that have expired."""

    to_update = []

    for record in (
        EmailVerification.objects.select_for_update()
        .filter(
            is_active=True,
            expiration_date__lte=timezone.now(),
        )
        .iterator()
    ):
        record.is_active = False
        to_update.append(record)

    EmailVerification.objects.bulk_update(objs=to_update, fields=["is_active"])


@CELERY_APP.task(name="change_status_of_expired_password_reset_records")
def change_status_of_expired_password_reset_records() -> None:
    """Change status of expired PasswordResetAttempt records to expired."""

    to_update = []

    for record in (
        PasswordResetAttempt.objects.select_for_update()
        .filter(
            status__in=[
                PasswordResetAttempt.STATUS_PENDING,
                PasswordResetAttempt.STATUS_OTP_VERIFIED,
            ],
            expiration_datetime__lte=timezone.now(),
        )
        .iterator()
    ):
        record.status = PasswordResetAttempt.STATUS_EXPIRED
        to_update.append(record)

    PasswordResetAttempt.objects.bulk_update(objs=to_update, fields=["status"])
