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
