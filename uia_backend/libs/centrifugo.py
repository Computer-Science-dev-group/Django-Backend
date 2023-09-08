import json
from logging import getLogger
from typing import Any

from cent import Client
from cent.core import CentException
from django.conf import settings

logger = getLogger()


class CentrifugoConnector:
    def __init__(self) -> None:
        cent_url = f"{settings.CENTRIFUGO_HOST}:{settings.CENTRIFUGO_PORT}/api"
        self.client = Client(
            cent_url,
            api_key=settings.CENTRIFUGO_API_KEY,
            timeout=1,
        )

    def publish_event(
        self,
        event_name: str,
        event_data: dict[str, Any],
        channel_name: str,
        **kwargs: dict[str, Any],
    ) -> None:
        """Publish event to centrifugo."""
        # https://centrifugal.dev/docs/3/server/server_api#publish

        try:
            payload = {"event": event_name, "data": event_data, **kwargs}
            self.client.publish(
                channel=channel_name, data=json.dumps(payload, default=str)
            )
        except (ValueError, CentException):
            logger.error(
                msg="uia_backend::libs::centrifugo::CentrifugoConnector::publish_event:: "
                "Error occured while publishing event",
                extra={
                    "event": event_name,
                    "data": event_data,
                    "channel": channel_name,
                    **kwargs,
                },
            )

    def broadcast_event(
        self,
        event_name: str,
        event_data: dict[str, Any],
        channels: list[str],
        **kwargs: dict[str, Any],
    ) -> None:
        """Broadcast event to multiple centrifugo channels."""
        # https://centrifugal.dev/docs/3/server/server_api#broadcast

        try:
            payload = {"event": event_name, "data": event_data, **kwargs}
            self.client.broadcast(
                channels=channels, data=json.dumps(payload, default=str)
            )
        except (ValueError, CentException):
            logger.error(
                msg="uia_backend::libs::centrifugo::CentrifugoConnector::broadcast_event:: "
                "Error occured while broadcasting event",
                extra={
                    "event": event_name,
                    "data": event_data,
                    "channels": channels,
                    **kwargs,
                },
            )

    def is_user_active(self, user_channel: str) -> bool:
        """Check if a user is online by retriving their private channel presence."""
        # https://centrifugal.dev/docs/3/server/server_api#presence

        try:
            response = self.client.presence(channel=user_channel)
        except (ValueError, CentException):
            response = {}
            logger.warning(
                msg="uia_backend::libs::centrifugo::CentrifugoConnector::is_user_active:: "
                "Error occured while checking users presence",
                extra={
                    "channel": user_channel,
                },
            )

        channel_presence = response.get("result", {})
        return (len(channel_presence.keys())) > 0
