from django.utils import timezone

from config.celery_app import app as CELERY_APP
from uia_backend.accounts.models import EmailVerification


@CELERY_APP.task(name="deactivate_expired_email_verification_records")
def deactivate_expired_email_verification_records() -> None:
    """Deactivate email verification records that have expired."""

    to_update = []

    for record in EmailVerification.objects.select_for_update().filter(
        is_active=True,
        expiration_date__lte=timezone.now(),
    ):
        record.is_active = False
        to_update.append(record)

    EmailVerification.objects.bulk_update(objs=to_update, fields=["is_active"])
