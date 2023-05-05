import logging
from typing import Any

from config.celery_app import app as CELERY_APP
from uia_backend.notification.utils.email_senders import SendInBlueEmailSender

Logger = logging.getLogger()


@CELERY_APP.task(name="send_email_task")
def send_template_email_task(
    recipients: list[str],
    internal_tracker_ids: str | list[str],
    template_id: str,
    template_merge_data: dict[str, Any],
):
    """Send template email task."""

    if isinstance(internal_tracker_ids, str):
        track_ids = [internal_tracker_ids for _ in range(len(recipients))]
    else:
        track_ids = internal_tracker_ids

    SendInBlueEmailSender().send_template_mail(
        recipients=recipients,
        internal_tracker_ids=track_ids,
        template_data=template_merge_data,
        template_id=template_id,
    )
