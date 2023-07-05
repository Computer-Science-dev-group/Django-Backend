import uuid

from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone
from factory.django import DjangoModelFactory

from uia_backend.notification.models import (
    EmailMessageModel,
    EmailTrackingModel,
    NotificationModel,
)


class EmailMessageModelFactory(DjangoModelFactory):
    esp = EmailMessageModel.ESP_TYPE_SENDINBLUE

    class Meta:
        model = EmailMessageModel


class EmailMessageModelTest(TestCase):
    def setUp(self) -> None:
        self.email_message = EmailMessageModelFactory.create(
            internal_tracker_id=uuid.uuid4(),
            message_id="xxxxxxxxxxxxx",
            message_type="Reset Password",
            recipient_email="user@example.com",
        )

    def test_unique_constraints(self):
        """Test unique constraints in model."""

        self.assertRaises(
            IntegrityError,
            EmailMessageModelFactory.create,
            esp=self.email_message.esp,
            message_id=self.email_message.message_id,
            recipient_email=self.email_message.recipient_email,
            internal_tracker_id=uuid.uuid4(),
            message_type="Reset Password",
        )


class EmailTrackingModelFactory(DjangoModelFactory):
    event_timestamp = timezone.now()

    class Meta:
        model = EmailTrackingModel


class NotificationModelFactory(DjangoModelFactory):
    class Meta:
        model = NotificationModel
