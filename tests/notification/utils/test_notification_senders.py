from unittest.mock import patch

from django.test import TestCase

from tests.accounts.test_models import UserModelFactory
from uia_backend.notification.utils.notification_senders import (
    InvalidEventError,
    Notifier,
)


class NotifierTests(TestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        self.target = UserModelFactory.create(email="target@example.com")

    def test_send_notification_with_send_in_app_notification_true(self):
        """Test send notification event with send_in_app_notification field set to true."""

        Notifier._Notifier__event_map["TEST_EVENT"]["send_in_app_notifcation"] = True
        event_data = {
            "recipients": [self.user],
            "verb": "Test notification",
            "metadata": {},
            "actor": None,
            "target": None,
        }

        with patch(
            "uia_backend.notification.tasks.send_in_app_notification_task.delay"
        ) as mock_send_in_app_notification:
            notifier = Notifier("TEST_EVENT", event_data)
            notifier.send_notification()

        mock_send_in_app_notification.assert_called_once_with(
            recipients=[self.user.id],
            data={},
            verb="Test notification",
            notification_type="TEST_EVENT",
            actor_dict=None,
            target_dict=None,
        )

    def test_send_notification_with_send_in_app_notification_false(self):
        """Test send notification event with send_in_app_notification field set to true."""

        Notifier._Notifier__event_map["TEST_EVENT"]["send_in_app_notifcation"] = False
        event_data = {
            "recipients": [self.user],
            "verb": "Test notification",
            "metadata": {},
            "actor": None,
            "target": None,
        }

        with patch(
            "uia_backend.notification.tasks.send_in_app_notification_task.delay"
        ) as mock_send_in_app_notification:
            notifier = Notifier("TEST_EVENT", event_data)
            notifier.send_notification()

        mock_send_in_app_notification.assert_not_called()

    def test_send_notification_with_send_push_notification_true(self):
        """Test send notification event with send_in_app_notification field set to true."""

        Notifier._Notifier__event_map["TEST_EVENT"]["send_push_notification"] = True
        event_data = {
            "recipients": [self.user],
            "verb": "Test notification",
            "metadata": {},
            "actor": None,
            "target": None,
        }

        with patch.object(
            Notifier, "_Notifier__send_push_notitfication"
        ) as mock_send_push_notitfication:
            notifier = Notifier("TEST_EVENT", event_data)
            notifier.send_notification()

        mock_send_push_notitfication.assert_called_once()

    def test_send_notification_with_send_push_notification_false(self):
        """Test send notification event with send_in_app_notification field set to false."""

        Notifier._Notifier__event_map["TEST_EVENT"]["send_push_notification"] = False
        event_data = {
            "recipients": [self.user],
            "verb": "Test notification",
            "metadata": {},
            "actor": None,
            "target": None,
        }

        with patch.object(
            Notifier, "_Notifier__send_push_notitfication"
        ) as mock_send_push_notitfication:
            notifier = Notifier("TEST_EVENT", event_data)
            notifier.send_notification()

        mock_send_push_notitfication.assert_not_called()

    def test_send_notification_with_invalid_event(self):
        """Send notification raise InvalidEventError if invalid event is passed."""

        event_data = {
            "recipients": [self.user.id],
            "verb": "Test notification",
            "metadata": {},
            "actor": None,
            "target": None,
        }

        # Assert that an InvalidEventError is raised when calling the send_notification method
        with self.assertRaises(InvalidEventError):
            # Create a Notifier instance with an invalid event
            Notifier("INVALID_EVENT", event_data)

    def test_send_notification_reduces_target_model_to_content_type_args(self):
        """
        Show that if target is paased to notification event data,
        it is reduced to NotificationContentTypeArgs before send_in_app_notification is called.
        """

        Notifier._Notifier__event_map["TEST_EVENT"]["send_in_app_notifcation"] = True
        event_data = {
            "recipients": [self.user],
            "verb": "Test notification",
            "metadata": {},
            "actor": None,
            "target": self.target,
        }

        with patch(
            "uia_backend.notification.tasks.send_in_app_notification_task.delay"
        ) as mock_send_in_app_notification:
            notifier = Notifier("TEST_EVENT", event_data)
            notifier.send_notification()

        mock_send_in_app_notification.assert_called_once_with(
            recipients=[self.user.id],
            data={},
            verb="Test notification",
            notification_type="TEST_EVENT",
            actor_dict=None,
            target_dict={
                "model_name": "customuser",
                "app_label": "accounts",
                "id": str(self.target.id),
            },
        )

    def test_send_notification_reduces_actor_model_to_content_type_args(self):
        """
        Show that if actor is paased to notification event data,
        it is reduced to NotificationContentTypeArgs before send_in_app_notification is called.
        """

        Notifier._Notifier__event_map["TEST_EVENT"]["send_in_app_notifcation"] = True
        event_data = {
            "recipients": [self.user],
            "verb": "Test notification",
            "metadata": {},
            "actor": self.user,
            "target": None,
        }

        with patch(
            "uia_backend.notification.tasks.send_in_app_notification_task.delay"
        ) as mock_send_in_app_notification:
            notifier = Notifier("TEST_EVENT", event_data)
            notifier.send_notification()

        mock_send_in_app_notification.assert_called_once_with(
            recipients=[self.user.id],
            data={},
            verb="Test notification",
            notification_type="TEST_EVENT",
            actor_dict={
                "model_name": "customuser",
                "app_label": "accounts",
                "id": str(self.user.id),
            },
            target_dict=None,
        )
