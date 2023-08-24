from typing import Any

import django
import jsonschema

from uia_backend.accounts.constants import NOTIFICATION_FIELD_SCHEMA


class JSONSchemaValidator:
    @staticmethod
    def validate(value: Any, schema: str, message: str | None = None):
        """Perform json schema validation"""
        try:
            jsonschema.validate(value, schema)
        except jsonschema.exceptions.ValidationError:
            raise django.core.exceptions.ValidationError(
                (message if message else "%(value)s failed JSON schema check"),
                params={"value": value},
            )


def validate_settings_notification(value: str):
    """Validate UserGenericSettings.notification field."""

    JSONSchemaValidator.validate(
        value=value,
        schema=NOTIFICATION_FIELD_SCHEMA,
        message="Notification field invalid.",
    )
