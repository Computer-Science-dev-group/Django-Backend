from typing import Any, TypedDict

from django.db.models import Model

from uia_backend.accounts.models import CustomUser
from uia_backend.notification import constants as notification_constants
from uia_backend.notification.tasks import send_in_app_notification_task


class EventData(TypedDict):
    """Notification event data."""

    recipients: list[CustomUser]
    verb: str
    metadata: dict[str, Any]
    actor: CustomUser | None
    target: Model | None


class EventSettings(TypedDict):
    """Event settings."""

    send_push_notification: bool
    send_in_app_notification: bool


class NotifierError(Exception):
    """Notifier exceptions"""


class InvalidEventError(NotifierError):
    """Invalid event passed to notifier"""


class Notifier:
    """
    The `Notifier` class is responsible for sending notifications to users based on different events.
    It uses a predefined event map to determine the settings for each event, such as whether
    to send in-app notifications or push notifications.
    """

    __event_map: dict[str, EventSettings] = {
        "TEST_EVENT": {
            "send_in_app_notification": True,
            "send_push_notification": False,
        },
        notification_constants.FOLLOW_USER_NOTIFICATION: {
            "send_in_app_notification": True,
            "send_push_notification": False,
        },
        notification_constants.UNFOLLOW_USER_NOTIFICATION: {
            "send_in_app_notification": True,
            "send_push_notification": False,
        },
        notification_constants.NOTIFICATION_TYPE_RECIEVED_CLUSTER_INVITATION: {
            "send_in_app_notification": True,
            "send_push_notification": False,
        },
        notification_constants.NOTIFICATION_TYPE_CANCELED_CLUSTER_INVITATION: {
            "send_in_app_notification": True,
            "send_push_notification": False,
        },
        notification_constants.NOTIFICATION_TYPE_ACCEPT_CLUSTER_INVITATION: {
            "send_in_app_notification": True,
            "send_push_notification": False,
        },
        notification_constants.NOTIFICATION_TYPE_REJECT_CLUSTER_INVITATION: {
            "send_in_app_notification": True,
            "send_push_notification": False,
        },
    }

    def __init__(self, event: str, data: EventData):
        """
        Initializes the `Notifier` instance with the event and event data.
        It also retrieves the event settings from the event map.

        Args:
            event (str): The name of the event.
            data (EventData): The data associated with the event.
        """

        self.event = event
        self.event_data = data

        try:
            self.event_settings = self.__event_map[event]
        except KeyError:
            raise InvalidEventError(
                f"Invalid event ensure that {event} can be handled by notifier."
            )

    def __send_push_notification(self) -> None:
        """
        Sends a push notification.
        This method is currently empty and needs to be implemented.
        """

    def __send_in_app_notification(self) -> None:
        """
        Sends an in-app notification.
        It extracts the necessary data from the event data and calls the `send_in_app_notification`
        function from the `uia_backend.notification.tasks` module.
        """

        target = self.event_data["target"]
        target_data = (
            {
                "model_name": target._meta.model_name,
                "app_label": target._meta.app_label,
                "id": str(target.id),
            }
            if target
            else None
        )

        actor = self.event_data["actor"]
        actor_data = (
            {
                "model_name": actor._meta.model_name,
                "app_label": actor._meta.app_label,
                "id": str(actor.id),
            }
            if actor
            else None
        )

        send_in_app_notification_task.delay(
            recipients=[recipient.id for recipient in self.event_data["recipients"]],
            data=self.event_data["metadata"],
            verb=self.event_data["verb"],
            notification_type=self.event,
            actor_dict=actor_data,
            target_dict=target_data,
        )

    def send_notification(self) -> None:
        """
        Sends the notification based on the event settings.
        It calls the `__send_in_app_notification` and `__send_push_notification` methods based on the event settings.
        """

        if self.event_settings["send_in_app_notification"]:
            self.__send_in_app_notification()

        if self.event_settings["send_push_notification"]:
            self.__send_push_notification()
