import uuid
from unittest.mock import patch

from django.test import TestCase, override_settings

from tests.accounts.test_models import UserModelFactory
from uia_backend.messaging.constants import CENT_EVENT_USER_NOTIFICATION
from uia_backend.notification.api.v1.serializers import NotificationSerializer
from uia_backend.notification.models import NotificationModel
from uia_backend.notification.tasks import (
    send_in_app_notification_task,
    send_template_email_task,
)


@override_settings(EMAIL_BACKEND="anymail.backends.sendinblue.EmailBackend")
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


class SendInAppNotificationTaskTests(TestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        self.target = UserModelFactory.create(email="target@example.com")

        self.target_data = {
            "model_name": "customuser",
            "app_label": "accounts",
            "id": str(self.target.id),
        }

        self.actor_data = {
            "model_name": "customuser",
            "app_label": "accounts",
            "id": str(self.user.id),
        }

    def test_send_in_app_notification(self):
        with patch(
            "uia_backend.libs.centrifugo.CentrifugoConnector.publish_event"
        ) as mock_publish_to_centrifugo:
            send_in_app_notification_task(
                recipients=[self.user.id],
                verb="Du hast",
                notification_type="",
                data={1: "Im gast"},
                actor_dict=self.actor_data,
                target_dict=self.target_data,
            )

        notification_records = NotificationModel.objects.filter(
            recipient=self.user,
            actor_object_id=self.user.id,
            target_object_id=self.target.id,
            verb="Du hast",
            type="",
            data={},
        )

        self.assertEqual(NotificationModel.objects.count(), 1)
        self.assertEqual(notification_records.count(), 1)

        mock_publish_to_centrifugo.assert_called_once_with(
            event_name=CENT_EVENT_USER_NOTIFICATION,
            channel_name=self.user.channel_name,
            event_data=dict(
                NotificationSerializer().to_representation(
                    instance=notification_records[0]
                )
            ),
        )
