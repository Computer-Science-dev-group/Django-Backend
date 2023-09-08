import logging
from typing import Any, TypedDict
from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from notifications.signals import notify

from config.celery_app import app as CELERY_APP
from uia_backend.accounts.models import CustomUser
from uia_backend.libs.centrifugo import CentrifugoConnector
from uia_backend.messaging.constants import CENT_EVENT_USER_NOTIFICATION
from uia_backend.notification.models import NotificationModel
from uia_backend.notification.utils.email_senders import (
    get_configured_email_service_provider_sender,
)

Logger = logging.getLogger()


@CELERY_APP.task(name="send_email_task")
def send_template_email_task(
    recipients: list[str],
    internal_tracker_ids: str | list[str],
    template_id: str,
    template_merge_data: dict[str, Any],
) -> None:
    """Send template email task."""

    if isinstance(internal_tracker_ids, str):
        track_ids = [internal_tracker_ids for _ in range(len(recipients))]
    else:
        track_ids = internal_tracker_ids

    sender_class = get_configured_email_service_provider_sender()
    sender_class().send_template_mail(
        recipients=recipients,
        internal_tracker_ids=track_ids,
        template_data=template_merge_data,
        template_id=template_id,
    )


def get_record_from_model_name(
    app_name: str, model_name: str, **kwargs
) -> Model | None:
    """Get record using content-type."""

    try:
        content_type = ContentType.objects.get(
            app_label=app_name.lower(),
            model=model_name,
        )
    except ContentType.DoesNotExist:
        Logger.error(
            "uia_backend::notification::tasks::get_record_from_model_name"
            "ContentType not found",
            extra={"app_label": app_name.lower(), "model": model_name},
        )

        return None

    try:
        record = content_type.get_object_for_this_type(**kwargs)
    except ObjectDoesNotExist:
        Logger.error(
            "uia_backend::notification::tasks::get_record_from_model_name:: "
            "Record not found",
            extra={
                "app_label": app_name.lower(),
                "model": model_name,
                "content_type": str(content_type.id),
                **kwargs,
            },
        )
        record = None

    return record


class NotificationContentTypeArgs(TypedDict):
    model_name: str
    app_label: str
    id: UUID


@CELERY_APP.task(name="send_in_app_notification_task")
def send_in_app_notification_task(
    recipients: list[UUID],
    verb: str,
    notification_type: str,
    data: dict[str, Any],
    actor_dict: NotificationContentTypeArgs | None,
    target_dict: NotificationContentTypeArgs | None,
) -> None:
    """Send in app notification."""

    # did this to avoid circular imports
    from uia_backend.notification.api.v1.serializers import NotificationSerializer

    cent_client = CentrifugoConnector()
    users = CustomUser.objects.filter(id__in=recipients)

    if actor_dict:
        actor = get_record_from_model_name(
            app_name=actor_dict["app_label"],
            model_name=actor_dict["model_name"],
            id=actor_dict["id"],
        )

    if target_dict:
        target = get_record_from_model_name(
            app_name=target_dict["app_label"],
            model_name=target_dict["model_name"],
            id=target_dict["id"],
        )

    for user in users:
        # create notification records on db
        recievers = notify.send(
            sender=actor if actor else user,
            recipient=user,
            verb=verb,
            data=data,
            type=notification_type,
            target=target,
        )

        try:
            notification_record = list(
                reciever[1][0]
                for reciever in recievers
                if isinstance(reciever[1][0], NotificationModel)
            )
        except IndexError:
            Logger.warning(
                "uia_backend::notification::tasks::send_in_app_notification_task:: "
                "Index error while parsing notification recievers",
                extra={
                    "recievers": str(recievers),
                },
            )

        if notification_record:
            # send event to centrifugo
            cent_client.publish_event(
                event_name=CENT_EVENT_USER_NOTIFICATION,
                channel_name=user.channel_name,
                event_data=dict(
                    NotificationSerializer().to_representation(
                        instance=notification_record[0]
                    )
                ),
            )
