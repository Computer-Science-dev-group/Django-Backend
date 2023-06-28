import logging
import random
from datetime import datetime, timedelta
from typing import Any

from django.contrib.auth.password_validation import password_changed, validate_password
from django.core import signing
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from uia_backend.accounts import constants
from uia_backend.accounts.models import (
    CustomUser,
    EmailVerification,
    FriendShip,
    FriendShipInvitation,
    PasswordResetAttempt,
    UserFriendShipSettings,
    UserHandle,
)
from uia_backend.accounts.utils import (
    generate_reset_password_otp,
    send_password_reset_otp_email_notification,
    send_user_password_change_email_notification,
    send_user_registration_email_verification_mail,
)
from uia_backend.cluster.utils import ClusterManager

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

        #  Below is for creation of user handle
        user_handle = (
            "@" + validated_data["first_name"] + "_" + validated_data["last_name"]
        )
        handle = UserHandle.objects.filter(user_handle=user_handle)
        if handle.exists():
            random_number = random.randrange(123, 567890)
            user_handle = (
                "@"
                + validated_data["first_name"]
                + "_"
                + validated_data["last_name"]
                + str(random_number)
            )
            print(f"user handle is {user_handle} after checking")
            UserHandle.objects.create(custom_user=user, user_handle=user_handle)
        else:
            print(f"user handle is {user_handle}")
            UserHandle.objects.create(custom_user=user, user_handle=user_handle)
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
        instance.user.save(update_fields=["is_active"])
        instance.save(update_fields=["is_active"])
        manager = ClusterManager(user=instance.user)
        manager.add_user_to_defualt_clusters()
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
        return {"message": "Your account has been successfully verified."}


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the Custom User Profile"""

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
            "faculty",
            "bio",
            "gender",
            "date_of_birth",
        ]
        read_only_fields = ["year_of_graduation", "department", "faculty"]

    def update(
        self, instance: CustomUser, validated_data: dict[str, Any]
    ) -> CustomUser:
        """
        Update the profile for an existing `CustomUser` instance, given the validated data.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Below is for changing user handle due to change in either first_name or last_name
        user_handle = (
            "@" + validated_data["first_name"] + "_" + validated_data["last_name"]
        )
        handle = UserHandle.objects.filter(user_handle=user_handle)
        if handle.exists():
            random_number = random.randrange(1234, 567890)
            user_handle = (
                "@"
                + validated_data["first_name"]
                + "_"
                + validated_data["last_name"]
                + str(random_number)
            )
            user = UserHandle.objects.get(custom_user=self.context['request'].user)
            user.user_handle = user_handle
            user.save()
        else:
            user = UserHandle.objects.get(custom_user=self.context['request'].user)
            user.user_handle = user_handle
            user.save()
        return instance


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
        return {"message": "Password Changed Successfully."}


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
            "Invalid credentials or your account is inactive."
        )

    def to_representation(self, instance: dict[str, Any]) -> dict[str, Any]:
        data = {"auth_token": str(AccessToken.for_user(user=instance["user"]))}
        return data


class RestPasswordRequestSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user__email", write_only=True)

    class Meta:
        model = PasswordResetAttempt
        fields = ["email"]

    def validate_email(self, value: str) -> CustomUser:
        """Validate that user with email exists."""
        user = CustomUser.objects.filter(email=value, is_active=True).first()

        if not user:
            raise serializers.ValidationError(
                "Invalid email address. No active user with this credentials was found."
            )

        return user

    def create(self, validated_data: dict[str, Any]) -> Any:
        """Create password reset attempt."""
        user = validated_data["user__email"]
        otp, signed_otp = generate_reset_password_otp()

        reset_record = PasswordResetAttempt.objects.create(
            user=user,
            signed_otp=signed_otp,
            expiration_datetime=timezone.now()
            + timedelta(minutes=constants.PASSWORD_RESET_ACTIVE_PERIOD),
        )
        send_password_reset_otp_email_notification(
            user=user, otp=otp, internal_tracker_id=reset_record.internal_tracker_id
        )
        return reset_record

    def update(
        self, instance: PasswordResetAttempt, validated_data: dict[str, Any]
    ) -> None:
        """Overiden method."""

    def to_representation(self, instance: PasswordResetAttempt) -> dict[str, Any]:
        return {"message": "OTP has been sent to this email address."}


class VerifyResetPasswordOTPSerializer(serializers.ModelSerializer):
    otp = serializers.CharField(
        source="signed_otp", max_length=6, min_length=6, write_only=True
    )
    email = serializers.EmailField(source="user__email", write_only=True)

    password_change_key = serializers.CharField(
        source="generate_signed_identifier", read_only=True
    )

    class Meta:
        model = PasswordResetAttempt
        fields = ["otp", "email", "password_change_key"]

    def validate_email(self, value: str) -> CustomUser:
        """Validate that user with email exists."""
        user = CustomUser.objects.filter(email=value, is_active=True).first()

        if not user:
            raise serializers.ValidationError(
                "Invalid email address. No active user with this credentials was found."
            )

        return user

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate otp sent is correct and not expired."""
        attrs = super().validate(attrs)

        user = attrs["user__email"]

        # validate otp
        signer = signing.Signer()
        signed_otp = signer.sign(attrs["signed_otp"])

        reset_record = PasswordResetAttempt.objects.filter(
            user=user,
            signed_otp=signed_otp,
            status=PasswordResetAttempt.STATUS_PENDING,
            expiration_datetime__gte=timezone.now(),
        ).first()

        if reset_record is None:
            raise serializers.ValidationError(
                {"otp": "Invalid otp or otp has expired."}
            )

        self.instance = reset_record
        return attrs

    def update(
        self, instance: PasswordResetAttempt, validated_data: dict[str, Any]
    ) -> PasswordResetAttempt:
        """Update record state."""
        instance.status = PasswordResetAttempt.STATUS_OTP_VERIFIED
        instance.save(update_fields=["status"])
        return instance

    def create(self, validated_data: Any) -> Any:
        """Overidden method."""


class ResetPasswordSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user__email", write_only=True)

    password_change_key = serializers.CharField(
        source="generate_signed_identifier", write_only=True
    )

    new_password = serializers.CharField(source="user__password", write_only=True)

    class Meta:
        model = PasswordResetAttempt
        fields = ["new_password", "email", "password_change_key"]

    def validate_email(self, value: str) -> CustomUser:
        """Validate that user with email exists."""
        user = CustomUser.objects.filter(email=value, is_active=True).first()

        if not user:
            raise serializers.ValidationError(
                "Invalid email address. No active user with this credentials was found."
            )

        return user

    def validate_new_password(self, value: str) -> str:
        """Validate new password."""

        try:
            validate_password(password=value)
        except ValidationError as error:
            raise serializers.ValidationError(error.error_list)

        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate password reset details."""

        attrs = super().validate(attrs)
        user = attrs["user__email"]

        signer = signing.TimestampSigner()

        try:
            record_id = signer.unsign(attrs["generate_signed_identifier"])
        except signing.BadSignature:
            raise serializers.ValidationError(
                {
                    "password_change_key": "Invalid password_change_key or session has expired. Please restart process."
                }
            )

        reset_record = PasswordResetAttempt.objects.filter(
            id=record_id,
            user=user,
            status=PasswordResetAttempt.STATUS_OTP_VERIFIED,
            expiration_datetime__gte=timezone.now(),
        ).first()

        if reset_record is None:
            raise serializers.ValidationError(
                {
                    "password_change_key": "Invalid password_change_key or session has expired. Please restart process."
                }
            )
        self.instance = reset_record
        return attrs

    def update(
        self, instance: PasswordResetAttempt, validated_data: dict[str, Any]
    ) -> PasswordResetAttempt:
        """Update record status and change users password."""
        instance.status = PasswordResetAttempt.STATUS_SUCCESS
        instance.user.set_password(validated_data["user__password"])

        instance.user.save(update_fields=["password"])
        instance.save(update_fields=["status"])

        return instance

    def to_representation(self, instance: PasswordResetAttempt) -> dict[str, str]:
        return {"message": "Password Reset Successfully."}


class FriendshipInvitationSerializer(serializers.ModelSerializer):
    sent_to = serializers.PrimaryKeyRelatedField(
        source="user",
        queryset=CustomUser.objects.filter(is_active=True, is_verified=True),
    )

    class Meta:
        model = FriendShipInvitation
        fields = [
            "id",
            "sent_to",
            "status",
            "created_by",
            "created_datetime",
            "updated_datetime",
        ]
        read_only_fields = ["id", "created_by", "created_datetime", "updated_datetime"]

    def validate_status(self, value: int) -> int:
        """Validate value of status."""
        instance: FriendShipInvitation | None = self.instance
        user = self.context["request"].user

        return_status = FriendShipInvitation.INVITATION_STATUS_PENDING

        if (
            instance
            and instance.status == FriendShipInvitation.INVITATION_STATUS_PENDING
        ):
            if user == instance.user and value in [
                FriendShipInvitation.INVITATION_STATUS_ACCEPTED,
                FriendShipInvitation.INVITATION_STATUS_REJECTED,
            ]:
                return_status = value
            elif (
                user == instance.created_by
                and value == FriendShipInvitation.INVITATION_STATUS_CANCLED
            ):
                return_status = value

        return return_status

    def validate_sent_to(self, value: CustomUser) -> CustomUser:
        """validate sent_to."""
        user = self.context["request"].user

        # ensure users can send invitations to thier self
        # ensure users cant send invitation to their friends
        if (user == value) or FriendShip.objects.filter(
            users__in=[user, value],
        ).exists():
            raise serializers.ValidationError(
                "Invalid user. Can not send inivitation to this user."
            )

        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate invitation data."""
        attrs = super().validate(attrs)

        # we want to ensure that user can creata a new invitation when one aready exits
        if (
            self.instance is None
            and FriendShipInvitation.objects.filter(
                created_by=self.context["request"].user,
                user=attrs["user"],
                status=FriendShipInvitation.INVITATION_STATUS_PENDING,
            ).exists()
        ):
            raise serializers.ValidationError(
                "Can not send new invitation. You already have a pending invitation sent to this user."
            )

        return attrs

    def update(
        self, instance: FriendShipInvitation, validated_data: dict[str, Any]
    ) -> FriendShipInvitation:
        """Update user invitation."""
        # we want to ensure only invitatio status can be updated
        validated_data.pop("user", None)

        # we want to ensure that we dont change anything
        # after status has transitioned from pending
        if instance.status != FriendShipInvitation.INVITATION_STATUS_PENDING:
            return instance

        super().update(instance, validated_data)
        if instance.status == FriendShipInvitation.INVITATION_STATUS_ACCEPTED:
            self.__accept_friendship_invitation(instance)

        return instance

    def __accept_friendship_invitation(
        self,
        instance: FriendShipInvitation,
    ) -> None:
        """Create friendship object when user accepts invitation."""

        friendship_record = FriendShip.objects.create()

        UserFriendShipSettings.objects.create(
            friendship=friendship_record,
            invitation=instance,
            user=instance.user,
        )
        UserFriendShipSettings.objects.create(
            friendship=friendship_record,
            invitation=instance,
            user=instance.created_by,
        )


class UserFriendShipSettingsSerializer(serializers.ModelSerializer):
    users = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(read_only=True),
        source="friendship__users",
    )

    class Meta:
        model = UserFriendShipSettings
        fields = ["id", "is_blocked", "users", "created_datetime", "updated_datetime"]
        read_only_fields = ["id", "created_datetime", "updated_datetime"]
