from dataclasses import dataclass
from typing import Any

from django.test import TestCase
from rest_framework.serializers import Serializer


@dataclass
class SerializerTestData:
    """Data class representing serializer data."""

    data: dict[str, Any]
    context: dict[str, Any]
    label: str


class CustomSerializerTests(TestCase):
    """
    The CustomSerializerTests class is a Django TestCase used for testing custom serializers.
    It contains methods for testing required and non-required fields, as well as valid and invalid data.
    The class is designed to be extended by specific serializer test cases,
    which define the serializer class, required and non-required fields, and valid and invalid data.
    """

    # NOTE : Ensure to set this to true when inheriing from this class
    __test__ = False
    serializer_class: Serializer

    REQUIRED_FIELDS: list[str]
    NON_REQUIRED_FIELDS: list

    VALID_DATA: list[SerializerTestData]
    INVALID_DATA: list[SerializerTestData]

    def test_required_fields(self):
        """Test serializer valid fields."""
        serializer = self.serializer_class()

        required_fields = []

        for field_name, field in serializer.get_fields().items():
            if field.required:
                required_fields.append(field_name)

        self.assertCountEqual(required_fields, self.REQUIRED_FIELDS)

        for field in self.REQUIRED_FIELDS:
            self.assertIn(
                field,
                required_fields,
                msg=f"Serializer field  `{field}` is not a required field.",
            )

    def test_non_required_fields(self):
        """Test non required fields."""
        serializer = self.serializer_class()

        non_required_fields = []
        for field_name, field in serializer.get_fields().items():
            if not field.required:
                non_required_fields.append(field_name)

        self.assertCountEqual(non_required_fields, self.NON_REQUIRED_FIELDS)

        for field in self.NON_REQUIRED_FIELDS:
            self.assertIn(
                field,
                non_required_fields,
                msg=f"Serializer field `{field}` is a required field.",
            )

    def test_valid_data(
        self,
    ):  # pragma: no cover # Difficult to test and not worth the effort
        """Test serializer valid data."""

        for valid_data in self.VALID_DATA:
            serializer = self.serializer_class(
                data=valid_data["data"], context=valid_data.get("context")
            )
            self.assertEqual(serializer.is_valid(), True, msg=valid_data.get("lable"))

    def test_invalid_data(
        self,
    ):  # pragma: no cover # Difficult to test and not worth the effort
        """Test serializer invalid data."""

        # NOTE: we might want to test error messages later
        for invalid_data in self.INVALID_DATA:
            serializer = self.serializer_class(
                data=invalid_data["data"],
                context=invalid_data.get("context"),
            )

            self.assertEqual(
                serializer.is_valid(),
                False,
                msg=invalid_data["lable"],
            )
