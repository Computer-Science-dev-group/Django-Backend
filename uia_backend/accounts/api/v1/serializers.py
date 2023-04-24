import logging
from datetime import datetime, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import password_changed, validate_password
from django.core import signing
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from uia_backend.accounts import constants
from uia_backend.accounts.models import OTP, CustomUser, EmailVerification
from uia_backend.accounts.utils import (
    send_user_forget_password_mail,
    send_user_password_change_email_notification,
    send_user_registration_email_verification_mail,
)
from uia_backend.libs.default_serializer import StructureSerializer

logger = logging.getLogger()


User = get_user_model()


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
        extra_kwargs = {"password": {"write_only": True}}

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

    def to_representation(self, instance: Any) -> Any:
        data = super().to_representation(instance)
        return StructureSerializer.to_representation(data)


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
        instance.user.save(update_fields=["is_active"])
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

    def to_representation(self, instance: Any) -> Any:
        data = "Your account has been successfully verified."
        return StructureSerializer.to_representation(data=data)


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("No user with this email address exists.")
        return email

    def save(self):
        email = self.validated_data["email"]
        user = CustomUser.objects.get(email=email)
        otp = get_random_string(
            length=constants.OTP_CHARACTER_LENGTH, allowed_chars="0123456789"
        )
        otp_expiry_time = timezone.now() + timezone.timedelta(minutes=30)
        OTP.objects.create(user=user, otp=otp, expiry_time=otp_expiry_time)
        send_user_forget_password_mail(user, request=self.context["request"], otp=otp)


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(max_length=40)

    def validate_email(self, email):
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("No user with this email address exists.")
        return email

    def validate(self, data):
        email = data["email"]
        otp = data["otp"]
        user = CustomUser.objects.get(email=email)

        # Get the most recent OTP for this user
        otp_obj = OTP.objects.filter(user=user).order_by("-expiry_time").first()
        if otp_obj.otp != otp:
            raise serializers.ValidationError("Invalid OTP.")
        if len(otp) > constants.OTP_CHARACTER_LENGTH:
            raise serializers.ValidationError("Invalid OTP.")
        # Checks if it has expired #NOTE: We could use a cron job for this task that sets the OTP to be invalid
        if timezone.now() > otp_obj.expiry_time:
            raise serializers.ValidationError("OTP has expired.")
        return data

    def save(self):
        email = self.validated_data["email"]
        user = CustomUser.objects.get(email=email)
        otp = self.validated_data["otp"]
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()

        # Makes it unusable
        otp_obj = OTP.objects.get(otp=otp)
        otp_obj.is_valid = False
        # NOTE: This is commented because we haven't set the Custom User as the auth model.
        # try:
        #     # Delete the previous token
        #     old_token = Token.objects.get(user=user)
        #     old_token.delete()

        # except Token.DoesNotExist:
        #     pass

        #     # Creates a new token
        # Token.objects.create(user=user)


class ChangePasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value: str) -> str:
        """Validate password value."""
        try:
            validate_password(password=value)
        except ValidationError as error:
            raise serializers.ValidationError(error.error_list)

        return value

    def create(self, validated_data: dict[str, Any]) -> None:
        """Overidden method."""

    def update(
        self, instance: CustomUser, validated_data: dict[str, Any]
    ) -> CustomUser:
        """Update users password."""
        instance.set_password(validated_data["password"])
        instance.save(update_fields=["password"])
        password_changed(user=instance, password=validated_data["password"])
        send_user_password_change_email_notification(
            instance, request=self.context["request"]
        )
        return instance

    def to_representation(self, instance: CustomUser) -> dict[str, Any]:
        data = "Password Changed Successfully."
        return StructureSerializer.to_representation(data=data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=250, required=True, write_only=True)
    password = serializers.CharField(max_length=250, required=True, write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate serializer data."""
        data = super().validate(attrs)

        # check that active user with this email exits
        user = CustomUser.objects.filter(email=data["email"], is_active=True).first()

        if user and user.check_password(raw_password=data["password"]):
            data["user"] = user
            return data
        raise serializers.ValidationError(
            "Invalid credentials or your accoun is inactive."
        )

    def to_representation(self, instance: dict[str, Any]) -> dict[str, Any]:
        data = {"auth_token": str(AccessToken.for_user(user=instance["user"]))}
        return StructureSerializer.to_representation(data=data)
