import logging
from typing import Any

# from django.core import mail
from django.core.mail import EmailMessage, get_connection

# from config.celery_app import app as CELERY_APP
from uia_backend.notification.models import EmailMessageModel

Logger = logging.getLogger()


class BaseEmailSender:
    def __init__(self) -> None:
        self.connection = get_connection()

    def send_template_mail(
        self,
        recipients: list[str],
        template_data: dict[str, Any],
        template_id: str,
        internal_tracker_ids: list[str],
    ) -> None:
        """Send single template mail."""


class SendInBlueEmailSender(BaseEmailSender):
    def _send_single_template_mail(
        self,
        recipient: str,
        template_id: str,
        internal_tracker_id: str,
        template_data: dict[str, Any],
        metadata: dict[str, Any] | None,
    ) -> None:
        """Send single template mail using sendinblue sender."""

        try:
            message = EmailMessage(to=[recipient], connection=self.connection)
            message.template_id = template_id
            message.merge_global_data = template_data
            message.metadata = metadata
            message.send()
        except Exception:
            Logger.error(
                msg=(
                    "uia_backend::notification::utils::email_senders::"
                    "SendInBlueEmailSender::send_single_template_mail:: Error occured while sending mail"
                ),
            )
            return

        EmailMessageModel.objects.create(
            esp=EmailMessageModel.ESP_TYPE_SENDINBLUE,
            internal_tracker_id=internal_tracker_id,
            message_id=message.anymail_status.message_id,
            recipient_email=recipient,
        )

    def send_template_mail(
        self,
        recipients: list[str],
        template_data: dict[str, Any],
        template_id: str,
        internal_tracker_ids: list[str],
    ) -> None:
        """send multiple template emails."""

        if len(internal_tracker_ids) != len(recipients):
            Logger.error(
                msg=(
                    "uia_backend::notification::utils::email_senders::"
                    "SendInBlueEmailSender::send_template_mail:: len(internal_tracker_ids) != len(recipients)"
                ),
            )
            raise AssertionError

        self.connection.open()
        for index, recipient in enumerate(recipients):
            self._send_single_template_mail(
                recipient=recipient,
                internal_tracker_id=internal_tracker_ids[index],
                template_id=template_id,
                template_data=template_data[recipient],
                metadata=None,
            )
        self.connection.close()
