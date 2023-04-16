"""
Test serializers for all models in UIA Django-Backend
"""

import pytest
from faker import Faker
from rest_framework import serializers

fake = Faker()


# Example serializer to show the working of the CustomSerializer class
class ExampleSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50, required=True)
    email = serializers.EmailField(max_length=254, required=False)


class CustomSerializerTester:
    """
    Custom Test class for any Serializer class
    """

    def test_required_fields(
        self, serializer_cls, valid_fields, invalid_fields, valid_data
    ):
        serializer = serializer_cls(data={})
        assert not serializer.is_valid()
        for field in valid_fields:
            assert field in serializer.errors

        serializer = serializer_cls(data=valid_data)
        assert serializer.is_valid()

    def test_valid_data(self, serializer_cls, valid_fields, valid_data):
        serializer = serializer_cls(data=valid_data)
        assert serializer.is_valid()

    def test_invalid_data(self, serializer_cls, invalid_fields, invalid_data):
        serializer = serializer_cls(data=invalid_data)
        assert not serializer.is_valid()


class TestExampleSerializer(CustomSerializerTester):
    @pytest.fixture
    def serializer_cls(self):
        return ExampleSerializer

    @pytest.fixture
    def valid_fields(self, serializer_cls):
        required_fields = []
        fields = serializer_cls().get_fields()
        for field_name, field in fields.items():
            if field.required:
                required_fields.append(f"{field_name}")
        return required_fields

    @pytest.fixture
    def invalid_fields(self, serializer_cls):
        non_required_fields = []
        fields = serializer_cls().get_fields()
        for field_name, field in fields.items():
            if not field.required:
                non_required_fields.append(f"{field_name}")
        return non_required_fields

    @pytest.fixture
    def valid_data(self, serializer_cls, valid_fields):
        fields = serializer_cls().get_fields()
        data = {}
        for field_name, _ in fields.items():
            key = f"{field_name}"
            value = getattr(fake, key)()
            data[key] = value
        return data

    @pytest.fixture
    def invalid_data(self, serializer_cls, invalid_fields):
        data = {}
        fields = serializer_cls().get_fields()
        for field_name, _ in fields.items():
            key = f"{field_name}"
            data[key] = None
        return data
