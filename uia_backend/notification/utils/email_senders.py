import logging
from typing import Any

from django.core.mail import EmailMessage, get_connection

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


# NOTE Joseph: this is not tested as it was implemented in an emergency
# NOTE Joseph: You need to also write a tracker for sendblue later
class SendGridEmailSender(BaseEmailSender):
    def __create_email_message_records(
        self,
        recipients: list[str],
        internal_tracker_ids: list[str],
        message: EmailMessage,
    ) -> None:
        to_create = []

        for index, recipient in enumerate(recipients):
            record = EmailMessageModel(
                esp=EmailMessageModel.ESP_TYPE_SENDGRID,
                internal_tracker_id=internal_tracker_ids[index],
                message_id=message.anymail_status.recipients[recipient].message_id,
                recipient_email=recipient,
            )
            to_create.append(record)

        EmailMessageModel.objects.bulk_create(objs=to_create)

    def send_template_mail(
        self,
        recipients: list[str],
        template_data: dict[str, Any],
        template_id: str,
        internal_tracker_ids: list[str],
    ) -> None:
        """Send multiple template emails over sendrid."""

        if len(internal_tracker_ids) != len(recipients):
            Logger.error(
                msg=(
                    "uia_backend::notification::utils::email_senders::"
                    "SendGridEmailSender::send_template_mail:: len(internal_tracker_ids) != len(recipients)"
                ),
            )
            raise AssertionError

        self.connection.open()
        try:
            message = EmailMessage(to=recipients)
            message.template_id = template_id
            message.merge_data = template_data
            message.send()
        except Exception as error:
            print(error)
            Logger.error(
                msg=(
                    "uia_backend::notification::utils::email_senders::"
                    "SendGridEmailSender::send_template_mail:: Error occured while sending mail"
                ),
                extra={"error_message": str(error)},
            )
            return
        self.connection.close()

        self.__create_email_message_records(
            recipients=recipients,
            internal_tracker_ids=internal_tracker_ids,
            message=message,
        )
