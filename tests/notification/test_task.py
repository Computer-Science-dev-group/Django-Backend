import uuid
from unittest.mock import patch

from django.test import TestCase

from uia_backend.notification.tasks import send_template_email_task


class TestSendTemplateEmailTask(TestCase):
    @patch(
        "uia_backend.notification.utils.email_senders.SendInBlueEmailSender.send_template_mail"
    )
    def test_method_success_with_single_tracking_id(self, mock_send_blue_sender):
        valid_data = {
            "recipients": ["u@example.com", "v@example.com"],
            "template_id": "111111111111",
            "internal_tracker_ids": str(uuid.uuid4()),
            "template_merge_data": {
                "u@example.com": {"name": "John Doe"},
                "v@example.com": {"name": "Van Dan"},
            },
        }

        send_template_email_task(**valid_data)

        mock_send_blue_sender.assert_called_once_with(
            recipients=valid_data["recipients"],
            internal_tracker_ids=[
                valid_data["internal_tracker_ids"],
                valid_data["internal_tracker_ids"],
            ],
            template_data=valid_data["template_merge_data"],
            template_id=valid_data["template_id"],
        )

    @patch(
        "uia_backend.notification.utils.email_senders.SendInBlueEmailSender.send_template_mail"
    )
    def test_method_success_with_multiple_tracking_id(self, mock_send_blue_sender):
        valid_data = {
            "recipients": ["u@example.com", "v@example.com"],
            "template_id": "111111111111",
            "internal_tracker_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
            "template_merge_data": {
                "u@example.com": {"name": "John Doe"},
                "v@example.com": {"name": "Van Dan"},
            },
        }

        send_template_email_task(**valid_data)

        mock_send_blue_sender.assert_called_once_with(
            recipients=valid_data["recipients"],
            internal_tracker_ids=valid_data["internal_tracker_ids"],
            template_data=valid_data["template_merge_data"],
            template_id=valid_data["template_id"],
        )
