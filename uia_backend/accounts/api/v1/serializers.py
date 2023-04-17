import logging
from datetime import datetime, timedelta
from typing import Any

from django.contrib.auth.password_validation import password_changed, validate_password
from django.core import signing
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

from uia_backend.accounts import constants
from uia_backend.accounts.models import CustomUser, EmailVerification
from uia_backend.accounts.utils import send_user_registration_email_verification_mail

logger = logging.getLogger()


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "faculty",
            "department",
            "year_of_graduation",
        ]

    def validate_password(self, value: str) -> str:
        """Validate password field."""
        try:
            validate_password(password=value)
        except ValidationError as error:
            raise serializers.ValidationError(error.error_list)

        return value

    def validate_year_of_graduation(self, value: str) -> str:
        """Validate year of graduation field."""

        error_message = "Invalid graduation year."

        if len(value) != 4:
            raise serializers.ValidationError(error_message)

        try:
            date_time_object = datetime.strptime(value, "%Y")
        except ValueError:
            raise serializers.ValidationError(error_message)

        if (
            date_time_object.year < int(constants.MIN_ALLOWED_GRADUATION_YEAR)
            or date_time_object.year > timezone.now().year
        ):
            raise serializers.ValidationError(error_message)

        return value

    def update(self, instance: CustomUser, validated_data: dict[str, Any]) -> None:
        """Overidden method."""

    def create(self, validated_data: dict[str, Any]) -> CustomUser:
        """Create User."""
        user = CustomUser.objects.create(**validated_data)
        user.set_password(validated_data["password"])
        user.save(update_fields=["password"])
        password_changed(user=user, password=validated_data["password"])
        send_user_registration_email_verification_mail(
            user, request=self.context["request"]
        )
        return user


class EmailVerificationSerializer(serializers.ModelSerializer):
    signature = serializers.CharField(
        max_length=500, required=True, write_only=True, source="id"
    )

    class Meta:
        model = EmailVerification
        fields = ["signature"]

    def create(self, validated_data: Any) -> None:
        """Overidden method."""

    def update(
        self, instance: EmailVerification, validated_data: dict[str, Any]
    ) -> None:
        """Update EmailVerification record."""
        instance.is_active = False
        instance.user.is_active = True
        instance.save(update_fields=["is_active"])
        instance.save(update_fields=["is_active"])
        return instance

    def validate(self, attrs: dict[str, Any]) -> EmailVerification:
        """Verify signature."""
        signature = attrs["id"]

        try:
            max_age = timedelta(hours=constants.EMAIL_VERIFICATION_ACTIVE_PERIOD)
            signer = signing.TimestampSigner()
            verification_id = signer.unsign_object(signature, max_age=max_age)
            self.instance = EmailVerification.objects.get(
                id=verification_id, is_active=True
            )
            return attrs
        except (signing.SignatureExpired, signing.BadSignature):
            raise serializers.ValidationError("Invalid link or link has expired.")
        except EmailVerification.DoesNotExist:
            logger.exception(
                "uia_backend::accounts::api::v1::serializers::validate:: Email verification record not found.",
                stack_info=True,
                extra={"details": verification_id},
            )
            raise serializers.ValidationError("Invalid link or link has expired.")


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the Custom User Profile"""

    year_of_graduation = serializers.CharField(max_length=4, read_only=True)
    department = serializers.CharField(max_length=65, read_only=True)
    faculty_or_college = serializers.CharField(max_length=65, read_only=True)


    class Meta:
        model = CustomUser
        fields = [
            "first_name", 
            "last_name", 
            "profile_picture", 
            "cover_photo",
            "phone_number",
            "display_name",
            "year_of_graduation",
            "department",
            "faculty_or_college",
            "bio", 
            "gender", 
            "date_of_birth",
        ]


    def update(self, instance: CustomUser, validated_data: dict[str, Any]) -> None:
        """
        Update the profile for an existing `CustomUser` instance, given the validated data.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
