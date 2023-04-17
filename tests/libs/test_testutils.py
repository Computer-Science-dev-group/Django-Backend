from django.test import TestCase
from rest_framework.serializers import Field, Serializer

from uia_backend.libs.testutils import CustomSerializerTests


class TestCustomSerializerTests(TestCase):
    def test_that_test_required_field_successful(self):
        """Test that required is correctly validated by the serializer test class."""

        # SETUP
        field1 = Field(required=True)
        field2 = Field(required=True)
        field3 = Field(required=False)

        mock_serializer_fields = {
            "field1": field1,
            "field2": field2,
            "field3": field3,
        }

        mock_serializer = Serializer

        setattr(mock_serializer, "get_fields", lambda self: mock_serializer_fields)

        test_class = CustomSerializerTests()
        test_class.REQUIRED_FIELDS = ["field1", "field2"]
        test_class.serializer_class = mock_serializer

        # TESTS
        # we should not have any assertions
        test_class.test_required_fields()

    def test_that_test_required_field_failed(self):
        """Test that required is correctly validated by the serializer test class."""

        # SETUP
        field1 = Field(required=True)
        field2 = Field(required=False)
        field3 = Field(required=False)

        mock_serializer_fields = {
            "field1": field1,
            "field2": field2,
            "field3": field3,
        }

        mock_serializer = Serializer

        setattr(mock_serializer, "get_fields", lambda self: mock_serializer_fields)

        test_class = CustomSerializerTests()
        test_class.REQUIRED_FIELDS = ["field1", "field2"]
        test_class.serializer_class = mock_serializer

        # TESTS
        # we should not have any assertions
        self.assertRaises(AssertionError, test_class.test_required_fields)

    def test_that_test_non_required_field_successful(self):
        """Test that non required is correctly validated by the serializer test class."""

        # SETUP
        field1 = Field(required=True)
        field2 = Field(required=False)
        field3 = Field(required=False)

        mock_serializer_fields = {
            "field1": field1,
            "field2": field2,
            "field3": field3,
        }

        mock_serializer = Serializer

        setattr(mock_serializer, "get_fields", lambda self: mock_serializer_fields)

        test_class = CustomSerializerTests()
        test_class.NON_REQUIRED_FIELDS = ["field3", "field2"]
        test_class.serializer_class = mock_serializer

        # TESTS
        # we should not have any assertions
        test_class.test_non_required_fields()

    def test_that_test_non_required_field_failed(self):
        """Test that non required is correctly validated by the serializer test class."""

        # SETUP
        field1 = Field(required=True)
        field2 = Field(required=False)
        field3 = Field(required=False)

        mock_serializer_fields = {
            "field1": field1,
            "field2": field2,
            "field3": field3,
        }

        mock_serializer = Serializer

        setattr(mock_serializer, "get_fields", lambda self: mock_serializer_fields)

        test_class = CustomSerializerTests()
        test_class.NON_REQUIRED_FIELDS = ["field3", "field2", "field1"]
        test_class.serializer_class = mock_serializer

        # TESTS
        self.assertRaises(AssertionError, test_class.test_non_required_fields)
