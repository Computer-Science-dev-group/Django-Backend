from django.db import models
from notifications.base.models import AbstractNotification

from uia_backend.libs.base_models import BaseAbstractModel
from uia_backend.notification.constants import NOTIFICATION_TYPE_CHOICES


class EmailMessageModel(BaseAbstractModel):
    """A model to represent an email message sent to a user."""

    ESP_TYPE_SENDINBLUE = 0
    ESP_TYPE_SENDGRID = 1

    ESP_TYPE_CHOICES = (
        (ESP_TYPE_SENDINBLUE, "SendInBlue"),
        (ESP_TYPE_SENDGRID, "SendGrid"),
    )

    EMAIL_MESSAGE_STATUS_PENDING = 0
    EMAIL_MESSAGE_STATUS_SENT = 1
    EMAIL_MESSAGE_STATUS_SUCCESS = 3
    EMAIL_MESSAGE_STATUS_FAILED = 4

    EMAIL_MESSAGE_STATUS_CHOICES = (
        (EMAIL_MESSAGE_STATUS_PENDING, "Pending: Email has been sent to the esp"),
        (EMAIL_MESSAGE_STATUS_SENT, "Sent: Email has been sent by the esp"),
        (EMAIL_MESSAGE_STATUS_SUCCESS, "Success: Email has been delivered to the user"),
        (
            EMAIL_MESSAGE_STATUS_FAILED,
            "Failed: Emails was not delivered or an error occured",
        ),
    )

    esp = models.CharField(
        choices=ESP_TYPE_CHOICES, default=ESP_TYPE_SENDINBLUE, max_length=100
    )
    internal_tracker_id = models.UUIDField(editable=False)
    message_id = models.CharField(editable=False, max_length=200)
    message_type = models.CharField(max_length=100, blank=True)
    status = models.IntegerField(
        choices=EMAIL_MESSAGE_STATUS_CHOICES,
        default=EMAIL_MESSAGE_STATUS_PENDING,
    )
    status_changes = models.JSONField(default=list)

    # NOTE: We can switch this for a foriegn key to the user model later
    recipient_email = models.EmailField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["esp", "message_id", "recipient_email"],
                name="message_id, recipient_email is unique together with esp",
            )
        ]


class EmailTrackingModel(BaseAbstractModel):
    """Model to store tracking data from anymail webhooks."""

    message = models.ForeignKey(EmailMessageModel, on_delete=models.CASCADE)
    event_timestamp = models.DateTimeField()
    event_type = models.CharField(max_length=200)
    metadata = models.JSONField(default=dict)
    rejection_reason = models.CharField(null=True, max_length=100)
    raw_event_data = models.JSONField(default=dict)


class NotificationModel(AbstractNotification, BaseAbstractModel):
    type = models.CharField(choices=NOTIFICATION_TYPE_CHOICES, max_length=50)
