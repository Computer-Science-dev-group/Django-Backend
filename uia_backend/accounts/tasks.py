from django.utils import timezone

from config.celery_app import app as CELERY_APP
from uia_backend.accounts.models import EmailVerification


@CELERY_APP.task(name="deactivate_expired_email_verification_records")
def deactivate_expired_email_verification_records() -> None:
    """Deactivate email verification records that have expired."""

    verification_records = EmailVerification.objects.select_for_update().filter(
        is_active=True,
        expiration_date__gt=timezone.now(),
    )

    for record in verification_records.iterator():
        record.is_active = False

    EmailVerification.objects.bulk_update(
        objs=verification_records, fields=["is_active"]
    )
