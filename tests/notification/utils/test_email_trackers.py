import uuid

from anymail.signals import AnymailTrackingEvent, tracking
from django.test import TestCase
from django.utils import timezone

from tests.notification.test_models import EmailMessageModelFactory
from uia_backend.notification import constants
from uia_backend.notification.models import EmailMessageModel, EmailTrackingModel
from uia_backend.notification.utils.email_tracking import SIBTrackingHandler


class SIBTrackingHandlerTests(TestCase):
    def setUp(self) -> None:
        self.email_message = EmailMessageModelFactory.create(
            message_id="test-message-id",
            recipient_email="user@example.com",
            internal_tracker_id=uuid.uuid4(),
        )

    def test_email_message_status_updated_successfully(self):
        """Test that the status of the associated email message is updated correctly based on the event type."""

        # setup
        event = AnymailTrackingEvent(
            event_type="delivered",
            message_id=self.email_message.message_id,
            recipient=self.email_message.recipient_email,
            timestamp=timezone.now(),
            metadata={},
            esp_event={},
        )

        handler = SIBTrackingHandler(event)

        # Test
        handler.signal_handeler()

        tracker = EmailTrackingModel.objects.filter(
            message=self.email_message,
            event_timestamp=event.timestamp,
            event_type=constants.EMAIL_EVENT_TYPE_DELIVERED,
            metadata=event.metadata,
            rejection_reason=None,
            raw_event_data=event.esp_event,
        ).first()

        self.assertIsNotNone(tracker)

        self.email_message.refresh_from_db()
        self.assertEqual(
            self.email_message.status, EmailMessageModel.EMAIL_MESSAGE_STATUS_SUCCESS
        )
        self.assertEqual(
            self.email_message.status_changes,
            [
                {
                    "from": EmailMessageModel.EMAIL_MESSAGE_STATUS_PENDING,
                    "to": EmailMessageModel.EMAIL_MESSAGE_STATUS_SUCCESS,
                }
            ],
        )

    def test_email_message_not_found(self):
        """Test that an error is logged when the associated email message is not found in the database."""

        event = AnymailTrackingEvent(
            event_type="delivered",
            message_id="xxxxxxxxxxxx",
            recipient="ccxxxx@example.com",
            timestamp=timezone.now(),
            metadata={},
            esp_event={},
        )

        with self.assertLogs(level="ERROR") as log:
            handler = SIBTrackingHandler(event)
            handler.signal_handeler()

        self.assertEqual(
            log.output[0],
            (
                "ERROR:root:"
                "uia_backend::libs::utils::emails::SIB_TrackingHandler::signal_handeler::"
                " EmailMessage record not found"
            ),
        )

    def test_event_type_not_allowed(self):
        """Test that an assertion error is raised when the event type is not in the allowed events list."""

        # Setup
        event = AnymailTrackingEvent(
            event_type="clicked",
            message_id=self.email_message.message_id,
            recipient=self.email_message.recipient_email,
            timestamp=timezone.now(),
            metadata={},
            esp_event={},
        )

        self.assertRaises(AssertionError, SIBTrackingHandler, event=event)

    def test_old_status_same_as_new_status(self):
        """
        Tests that the status of the associated email message is not
        updated when the old status is the same as the new status.
        """

        self.email_message.status = EmailMessageModel.EMAIL_MESSAGE_STATUS_SUCCESS
        self.email_message.save()

        event = AnymailTrackingEvent(
            event_type="delivered",
            message_id=self.email_message.message_id,
            recipient=self.email_message.recipient_email,
            timestamp=timezone.now(),
            metadata={},
            esp_event={},
        )

        handler = SIBTrackingHandler(event)

        handler.signal_handeler()

        tracker = EmailTrackingModel.objects.filter(
            message=self.email_message,
            event_timestamp=event.timestamp,
            event_type=constants.EMAIL_EVENT_TYPE_DELIVERED,
            metadata=event.metadata,
            rejection_reason=None,
            raw_event_data=event.esp_event,
        ).first()

        self.assertIsNotNone(tracker)

        self.email_message.refresh_from_db()
        self.assertEqual(
            self.email_message.status, EmailMessageModel.EMAIL_MESSAGE_STATUS_SUCCESS
        )

    def test_successful_tracking(self):
        """
        Tests that email message status is updated
        correctly when the event type is "delivered" or "opened"
        """

        # setup
        event = AnymailTrackingEvent(
            event_type="opened",
            message_id=self.email_message.message_id,
            recipient=self.email_message.recipient_email,
            timestamp=timezone.now(),
            metadata={},
            esp_event={},
        )

        handler = SIBTrackingHandler(event)

        # Test
        handler.signal_handeler()

        tracker = EmailTrackingModel.objects.filter(
            message=self.email_message,
            event_timestamp=event.timestamp,
            event_type=constants.EMAIL_EVENT_TYPE_OPENED,
            metadata=event.metadata,
            rejection_reason=None,
            raw_event_data=event.esp_event,
        ).first()

        self.assertIsNotNone(tracker)

        self.email_message.refresh_from_db()
        self.assertEqual(
            self.email_message.status, EmailMessageModel.EMAIL_MESSAGE_STATUS_SUCCESS
        )
        self.assertEqual(
            self.email_message.status_changes,
            [
                {
                    "from": EmailMessageModel.EMAIL_MESSAGE_STATUS_PENDING,
                    "to": EmailMessageModel.EMAIL_MESSAGE_STATUS_SUCCESS,
                }
            ],
        )

    def test_failed_tracking(self):
        """
        Tests that email message status is updated correctly
        when the event type is "bounced" or "rejected
        """

        # setup
        bounced_event = AnymailTrackingEvent(
            event_type="bounced",
            message_id=self.email_message.message_id,
            recipient=self.email_message.recipient_email,
            timestamp=timezone.now(),
            metadata={},
            esp_event={},
        )

        rejected_event = AnymailTrackingEvent(
            event_type="rejected",
            message_id=self.email_message.message_id,
            recipient=self.email_message.recipient_email,
            timestamp=timezone.now(),
            metadata={},
            esp_event={},
        )

        handler = SIBTrackingHandler(bounced_event)

        # Test
        handler.signal_handeler()

        tracker = EmailTrackingModel.objects.filter(
            message=self.email_message,
            event_timestamp=bounced_event.timestamp,
            event_type=constants.EMAIL_EVENT_TYPE_BOUNCED,
            metadata=bounced_event.metadata,
            rejection_reason=None,
            raw_event_data=bounced_event.esp_event,
        ).first()

        self.assertIsNotNone(tracker)

        self.email_message.refresh_from_db()
        self.assertEqual(
            self.email_message.status, EmailMessageModel.EMAIL_MESSAGE_STATUS_FAILED
        )
        self.assertEqual(
            self.email_message.status_changes,
            [
                {
                    "from": EmailMessageModel.EMAIL_MESSAGE_STATUS_PENDING,
                    "to": EmailMessageModel.EMAIL_MESSAGE_STATUS_FAILED,
                }
            ],
        )

        handler = SIBTrackingHandler(rejected_event)

        handler.signal_handeler()

        tracker = EmailTrackingModel.objects.filter(
            message=self.email_message,
            event_timestamp=rejected_event.timestamp,
            event_type=constants.EMAIL_EVENT_TYPE_REJECTED,
            metadata=rejected_event.metadata,
            rejection_reason=None,
            raw_event_data=rejected_event.esp_event,
        ).first()

        self.assertIsNotNone(tracker)

        self.email_message.refresh_from_db()
        self.assertEqual(
            self.email_message.status, EmailMessageModel.EMAIL_MESSAGE_STATUS_FAILED
        )
        self.assertEqual(
            self.email_message.status_changes,
            [
                {
                    "from": EmailMessageModel.EMAIL_MESSAGE_STATUS_PENDING,
                    "to": EmailMessageModel.EMAIL_MESSAGE_STATUS_FAILED,
                }
            ],
        )

    def test_queued_tracking(self):
        """Tests that email message status is updated correctly when the event type is "queued" """

        event = AnymailTrackingEvent(
            event_type="queued",
            message_id=self.email_message.message_id,
            recipient=self.email_message.recipient_email,
            timestamp=timezone.now(),
            metadata={},
            esp_event={},
        )

        handler = SIBTrackingHandler(event)

        # Test
        handler.signal_handeler()

        tracker = EmailTrackingModel.objects.filter(
            message=self.email_message,
            event_timestamp=event.timestamp,
            event_type=constants.EMAIL_EVENT_TYPE_QUEUED,
            metadata=event.metadata,
            rejection_reason=None,
            raw_event_data=event.esp_event,
        ).first()

        self.assertIsNotNone(tracker)

        self.email_message.refresh_from_db()
        self.assertEqual(
            self.email_message.status, EmailMessageModel.EMAIL_MESSAGE_STATUS_SENT
        )
        self.assertEqual(
            self.email_message.status_changes,
            [
                {
                    "from": EmailMessageModel.EMAIL_MESSAGE_STATUS_PENDING,
                    "to": EmailMessageModel.EMAIL_MESSAGE_STATUS_SENT,
                }
            ],
        )


class SignalReceiverTests(TestCase):
    def setUp(self) -> None:
        self.email_message = EmailMessageModelFactory.create(
            message_id="test-message-id",
            recipient_email="user@example.com",
            internal_tracker_id=uuid.uuid4(),
        )

    def test_SIB_signal_processed_successfully(self):
        """Test that the signal was successfuly processed by SIBTrackingHandler"""

        event = AnymailTrackingEvent(
            event_type="delivered",
            message_id=self.email_message.message_id,
            recipient=self.email_message.recipient_email,
            timestamp=timezone.now(),
            metadata={},
            esp_event={},
        )

        tracking.send(sender=object(), event=event, esp_name="SendinBlue")

        tracker = EmailTrackingModel.objects.filter(
            message=self.email_message,
            event_timestamp=event.timestamp,
            event_type=constants.EMAIL_EVENT_TYPE_DELIVERED,
            metadata=event.metadata,
            rejection_reason=None,
            raw_event_data=event.esp_event,
        ).first()

        self.assertIsNotNone(tracker)

        self.email_message.refresh_from_db()
        self.assertEqual(
            self.email_message.status, EmailMessageModel.EMAIL_MESSAGE_STATUS_SUCCESS
        )
        self.assertEqual(
            self.email_message.status_changes,
            [
                {
                    "from": EmailMessageModel.EMAIL_MESSAGE_STATUS_PENDING,
                    "to": EmailMessageModel.EMAIL_MESSAGE_STATUS_SUCCESS,
                }
            ],
        )
