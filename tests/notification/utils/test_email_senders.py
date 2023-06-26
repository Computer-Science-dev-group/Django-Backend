import uuid
from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings

from uia_backend.notification.models import EmailMessageModel
from uia_backend.notification.utils.email_senders import (
    SendGridEmailSender,
    SendInBlueEmailSender,
)


@override_settings(EMAIL_BACKEND="anymail.backends.test.EmailBackend")
class SendInBlueEmailSenderTests(TestCase):
    def setUp(self) -> None:
        self.email_sender = SendInBlueEmailSender()

    def test_send_single_template_mail__sends_email_successful(self):
        """Test to validated that _send_single_template_mail method works correctly."""

        valid_data = {
            "recipient": "user@example.com",
            "template_id": "111111111111",
            "internal_tracker_id": uuid.uuid4(),
            "template_data": {"name": "John Doe"},
            "metadata": None,
        }

        self.email_sender._send_single_template_mail(**valid_data)

        self.assertEqual(len(mail.outbox), 1)
        _mail = mail.outbox[0]
        # Verify attributes of the EmailMessage that was sent:
        self.assertEqual(_mail.to, ["user@example.com"])
        self.assertEqual(_mail.template_id, valid_data["template_id"])
        self.assertEqual(_mail.merge_global_data, valid_data["template_data"])
        self.assertEqual(_mail.metadata, valid_data["metadata"])
        self.assertIsNotNone(_mail.anymail_status.message_id)

        message = EmailMessageModel.objects.filter(
            esp=EmailMessageModel.ESP_TYPE_SENDINBLUE,
            internal_tracker_id=valid_data["internal_tracker_id"],
        ).first()

        self.assertIsNotNone(message)
        self.assertEqual(message.internal_tracker_id, valid_data["internal_tracker_id"])
        self.assertEqual(message.recipient_email, valid_data["recipient"])
        self.assertEqual(str(message.message_id), str(_mail.anymail_status.message_id))

    @patch("django.core.mail.EmailMessage.send")
    def test_send_single_template_mail__sends_email_error(self, mock_email_send):
        """Test to validate that _send_single_template_mail handels errors properly."""

        valid_data = {
            "recipient": "user@example.com",
            "template_id": "111111111111",
            "internal_tracker_id": uuid.uuid4(),
            "template_data": {"name": "John Doe"},
            "metadata": None,
        }

        mock_email_send.side_effect = Exception

        with self.assertLogs(level="ERROR") as log:
            self.email_sender._send_single_template_mail(**valid_data)

        self.assertEqual(
            log.output[0],
            (
                "ERROR:root:"
                "uia_backend::notification::utils::email_senders::"
                "SendInBlueEmailSender::send_single_template_mail:: Error occured while sending mail"
            ),
        )

    def test_send_template_mail_successful(self):
        """Test to validate that send_template_mail method works correcly."""

        valid_data = {
            "recipients": ["u@example.com", "v@example.com"],
            "template_id": "111111111111",
            "internal_tracker_ids": [uuid.uuid4(), uuid.uuid4()],
            "template_data": {
                "u@example.com": {"name": "John Doe"},
                "v@example.com": {"name": "Van Dan"},
            },
        }

        self.email_sender.send_template_mail(**valid_data)

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(mail.outbox[0].to[0], valid_data["recipients"])
        self.assertIn(mail.outbox[1].to[0], valid_data["recipients"])

        self.assertEqual(
            EmailMessageModel.objects.filter(
                esp=EmailMessageModel.ESP_TYPE_SENDINBLUE,
            ).count(),
            2,
        )

        message_1 = EmailMessageModel.objects.filter(
            esp=EmailMessageModel.ESP_TYPE_SENDINBLUE,
            internal_tracker_id=valid_data["internal_tracker_ids"][0],
        ).first()
        message_2 = EmailMessageModel.objects.filter(
            esp=EmailMessageModel.ESP_TYPE_SENDINBLUE,
            internal_tracker_id=valid_data["internal_tracker_ids"][1],
        ).first()

        self.assertIsNotNone(message_1)
        self.assertIsNotNone(message_2)

        self.assertEqual(message_1.recipient_email, valid_data["recipients"][0])
        self.assertEqual(
            str(message_1.message_id), str(mail.outbox[0].anymail_status.message_id)
        )

        self.assertEqual(message_2.recipient_email, valid_data["recipients"][1])
        self.assertEqual(
            str(message_2.message_id), str(mail.outbox[1].anymail_status.message_id)
        )

    def test_send_template_mail_error_due_to_internal_tracker_ids_lenegth(self):
        """
        Test to assert thet send_template_mail raises
        AssertionError when len(internal_tracker_ids) != len(recipients).
        """

        valid_data = {
            "recipients": ["u@example.com", "v@example.com"],
            "template_id": "111111111111",
            "internal_tracker_ids": [uuid.uuid4()],
            "template_data": {
                "u@example.com": {"name": "John Doe"},
                "v@example.com": {"name": "Van Dan"},
            },
        }

        with self.assertLogs(level="ERROR") as log, self.assertRaises(AssertionError):
            self.email_sender.send_template_mail(**valid_data)

        self.assertEqual(
            log.output[0],
            (
                "ERROR:root:"
                "uia_backend::notification::utils::email_senders::"
                "SendInBlueEmailSender::send_template_mail:: len(internal_tracker_ids) != len(recipients)"
            ),
        )


@override_settings(EMAIL_BACKEND="anymail.backends.test.EmailBackend")
class SendGridEmailSenderTests(TestCase):
    def setUp(self) -> None:
        self.email_sender = SendGridEmailSender()

    def test_send_template_mail(self):
        """Test to validated that _send_template_mail method works correctly."""

        valid_data = {
            "recipients": ["user@example.com"],
            "template_data": {"name": "John Doe"},
            "template_id": "111111111111",
            "internal_tracker_ids": [uuid.uuid4()],
        }

        self.email_sender.send_template_mail(**valid_data)
        _mail = mail.outbox[0]
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(_mail.to, ["user@example.com"])
        self.assertEqual(_mail.template_id, valid_data["template_id"])
        self.assertEqual(_mail.merge_data, valid_data["template_data"])

        message = EmailMessageModel.objects.filter(
            esp=EmailMessageModel.ESP_TYPE_SENDGRID,
            internal_tracker_id=valid_data["internal_tracker_ids"][0],
        ).first()

        self.assertIsNotNone(message)
        self.assertEqual(message.recipient_email, valid_data["recipients"][0])
        self.assertEqual(str(message.message_id), str(_mail.anymail_status.message_id))

    @patch("django.core.mail.EmailMessage.send")
    def test_send_template_mail__sends_email_error(self, mock_email_send):
        """Test to validate that _send_single_template_mail handels errors properly."""

        valid_data = {
            "recipients": ["user@example.com"],
            "template_id": "111111111111",
            "internal_tracker_ids": [uuid.uuid4()],
            "template_data": {"name": "John Doe"},
        }

        mock_email_send.side_effect = Exception

        with self.assertLogs(level="ERROR") as log:
            self.email_sender.send_template_mail(**valid_data)

        self.assertEqual(
            log.output[0],
            (
                "ERROR:root:"
                "uia_backend::notification::utils::email_senders::"
                "SendGridEmailSender::send_template_mail:: Error occured while sending mail"
            ),
        )

    @patch("django.core.mail.EmailMessage.send")
    def test_send_template_mail_sends_email_error_due_to_internal_tracker_ids_length(
        self, mock_email_send
    ):
        """Test to validate that _send_template_mail handels errors properly."""

        valid_data = {
            "recipients": ["u@example.com", "v@example.com"],
            "template_id": "111111111111",
            "internal_tracker_ids": [uuid.uuid4()],
            "template_data": {
                "u@example.com": {"name": "John Doe"},
                "v@example.com": {"name": "Van Dan"},
            },
        }

        mock_email_send.side_effect = Exception

        with self.assertLogs(level="ERROR") as log, self.assertRaises(AssertionError):
            self.email_sender.send_template_mail(**valid_data)

        self.assertEqual(
            log.output[0],
            (
                "ERROR:root:"
                "uia_backend::notification::utils::email_senders::"
                "SendGridEmailSender::send_template_mail:: len(internal_tracker_ids) != len(recipients)"
            ),
        )
