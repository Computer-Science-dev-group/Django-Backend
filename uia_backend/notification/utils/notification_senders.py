from typing import Any

from django.db.models import Model
from notifications.signals import notify

from uia_backend.accounts.models import CustomUser


def send_in_app_notifcation(
    recipient: CustomUser,
    sender: Model,
    verb: str,
    type: str,
    metadata: dict[str, Any] | None = None,
    **kwargs,
):
    """Send in app notification to a user."""

    notify.send(
        sender=sender,
        recipient=recipient,
        verb=verb,
        data=metadata,
        type=type,
        **kwargs,
    )
