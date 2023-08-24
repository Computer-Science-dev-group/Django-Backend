import logging

from anymail.backends.sendgrid import EmailBackend as SendGrid_EmailBackend
from anymail.backends.sendinblue import EmailBackend as SIB_EmailBackend
from anymail.signals import AnymailTrackingEvent, tracking
from django.dispatch import receiver

from uia_backend.notification import constants as email_constants
from uia_backend.notification.models import EmailMessageModel, EmailTrackingModel

Logger = logging.getLogger()


@receiver(tracking, dispatch_uid="anymail_signale")
def signal_receiver(sender, event: AnymailTrackingEvent, esp_name: str, **kwargs):
    """Receiver anymail signals."""

    if (
        esp_name == SIB_EmailBackend.esp_name
        and event.event_type in SIBTrackingHandler._allowed_events
    ):
        SIBTrackingHandler(event).signal_handeler()
    elif (
        esp_name == SendGrid_EmailBackend.esp_name
        and event.event_type in SendGridTrackingHandler._allowed_events
    ):
        SendGridTrackingHandler(event).signal_handeler()


class BaseEmailTrackingHandler:
    _allowed_events: tuple[str]
    event: AnymailTrackingEvent

    def __init__(self, event: AnymailTrackingEvent) -> None:
        self.event = event

        if event.event_type not in self._allowed_events:
            raise AssertionError("Invalid event")

    def signal_handler(self):
        """Handle anymail webhook signal."""


class SIBTrackingHandler(BaseEmailTrackingHandler):
    _allowed_events = (
        "queued",
        "rejected",
        "bounced",
        "deferred",
        "delivered",
        "opened",
    )
    _event_mapping = {
        "queued": email_constants.EMAIL_EVENT_TYPE_QUEUED,
        "rejected": email_constants.EMAIL_EVENT_TYPE_REJECTED,
        "bounced": email_constants.EMAIL_EVENT_TYPE_BOUNCED,
        "deferred": email_constants.EMAIL_EVENT_TYPE_DEFFERED,
        "delivered": email_constants.EMAIL_EVENT_TYPE_DELIVERED,
        "opened": email_constants.EMAIL_EVENT_TYPE_OPENED,
    }

    def _update_email_message(self, message: EmailMessageModel) -> None:
        """Update the status of the associated email message."""

        event = self._resolve_event_type()
        old_status = message.status
        new_status = message.status

        if event in (
            email_constants.EMAIL_EVENT_TYPE_DELIVERED,
            email_constants.EMAIL_EVENT_TYPE_OPENED,
        ):
            new_status = EmailMessageModel.EMAIL_MESSAGE_STATUS_SUCCESS
        elif event in (
            email_constants.EMAIL_EVENT_TYPE_BOUNCED,
            email_constants.EMAIL_EVENT_TYPE_REJECTED,
        ):
            new_status = EmailMessageModel.EMAIL_MESSAGE_STATUS_FAILED
        elif event == email_constants.EMAIL_EVENT_TYPE_QUEUED:
            new_status = EmailMessageModel.EMAIL_MESSAGE_STATUS_SENT
        else:
            new_status = EmailMessageModel.EMAIL_MESSAGE_STATUS_PENDING

        if old_status != new_status:
            message.status = new_status
            message.status_changes.append({"from": old_status, "to": new_status})
            message.save(update_fields=["status", "status_changes"])

    def _resolve_event_type(self) -> int:
        """"""
        return self._event_mapping[self.event.event_type]

    def signal_handeler(self) -> None:
        """Handle sendinblue anymail signals."""

        message = EmailMessageModel.objects.filter(
            esp=EmailMessageModel.ESP_TYPE_SENDINBLUE,
            message_id=self.event.message_id,
        ).first()

        if message is None:
            Logger.error(
                (
                    "uia_backend::libs::utils::emails::SIB_TrackingHandler::signal_handeler::"
                    " EmailMessage record not found"
                ),
                extra={
                    "esp": EmailMessageModel.ESP_TYPE_SENDINBLUE,
                    "message_id": self.event.message_id,
                },
            )
            return

        EmailTrackingModel.objects.create(
            message=message,
            event_timestamp=self.event.timestamp,
            event_type=self._resolve_event_type(),
            metadata=self.event.metadata,
            rejection_reason=self.event.reject_reason,
            raw_event_data=self.event.esp_event,
        )

        self._update_email_message(message)


class SendGridTrackingHandler(BaseEmailTrackingHandler):
    _allowed_events = ("delivered", "bounced", "opened", "deferred")
    _event_mapping = {
        "delivered": email_constants.EMAIL_EVENT_TYPE_DELIVERED,
        "bounced": email_constants.EMAIL_EVENT_TYPE_BOUNCED,
        "deferred": email_constants.EMAIL_EVENT_TYPE_DEFFERED,
        "opened": email_constants.EMAIL_EVENT_TYPE_OPENED,
    }

    def _update_email_message(self, message: EmailMessageModel) -> None:
        """Update the status of the associated email message"""

        event = self._resolve_event_type()
        old_status = message.status
        new_status = message.status

        if event in (
            email_constants.EMAIL_EVENT_TYPE_DELIVERED,
            email_constants.EMAIL_EVENT_TYPE_OPENED,
        ):
            new_status = EmailMessageModel.EMAIL_MESSAGE_STATUS_SUCCESS

        elif event in (
            email_constants.EMAIL_EVENT_TYPE_BOUNCED,
            email_constants.EMAIL_EVENT_TYPE_REJECTED,
        ):
            new_status = EmailMessageModel.EMAIL_MESSAGE_STATUS_FAILED
        else:
            new_status = EmailMessageModel.EMAIL_MESSAGE_STATUS_PENDING

        if old_status != new_status:
            message.status = new_status
            message.status_changes.append({"from": old_status, "to": new_status})
            message.save(update_fields=["status", "status_changes"])

    def _resolve_event_type(self) -> int:
        """This returns the event type"""
        return self._event_mapping[self.event.event_type]

    def signal_handeler(self) -> None:
        """Handles sendgrid anymail signals"""
        message = EmailMessageModel.objects.filter(
            esp=EmailMessageModel.ESP_TYPE_SENDGRID, message_id=self.event.message_id
        ).first()

        if message is None:
            Logger.error(
                (
                    "uia_backend::libs::utils::emails::SendGridTrackingHandler::signal_handler::"
                    "EmailMessage record not found"
                ),
                extra={
                    "esp": EmailMessageModel.ESP_TYPE_SENDGRID,
                    "message_id": self.event.message_id,
                },
            )
            return

        EmailTrackingModel.objects.create(
            message=message,
            event_timestamp=self.event.timestamp,
            event_type=self._resolve_event_type(),
            metadata=self.event.metadata,
            rejection_reason=self.event.reject_reason,
            raw_event_data=self.event.esp_event,
        )

        self._update_email_message(message)
