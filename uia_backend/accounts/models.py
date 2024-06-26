import uuid

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core import signing
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _

from uia_backend.libs.base_models import BaseAbstractModel
from uia_backend.libs.validators import validate_settings_notification


def user_profile_upload_location(instance, filename: str) -> str:
    """Get Location for user profile photo upload."""
    return f"users/{instance.id}/profile/{filename}"


def user_cover_profile_upload_location(instance, filename: str) -> str:
    """Get location for user profile cover photo upload."""
    return f"users/{instance.id}/cover/{filename}"


class CustomUserManager(BaseUserManager):
    """Custom User Manager for UIA User Model"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class CustomUser(BaseAbstractModel, AbstractBaseUser, PermissionsMixin):
    """Custom User model for UIA"""

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    display_name = models.CharField(max_length=150)
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    password = models.CharField(max_length=128)
    profile_picture = models.ImageField(
        upload_to=user_profile_upload_location, null=True
    )
    cover_photo = models.ImageField(
        upload_to=user_cover_profile_upload_location, null=True
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    faculty = models.CharField(max_length=60)
    department = models.CharField(max_length=60)
    year_of_graduation = models.CharField(max_length=4)
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True)
    app_version = models.CharField(max_length=100, blank=True, null=True)
    follows = models.ManyToManyField(
        "self", symmetrical=False, related_name="followers", through="Follows"
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "faculty",
        "department",
        "year_of_graduation",
    ]

    def __str__(self) -> str:
        return self.email

    @property
    def channel_name(self) -> str:
        return f"${settings.USER_NAMESPACE}:{self.id}#{self.id}"


class Follows(BaseAbstractModel):
    """Model that represents a follow relationship between two users."""

    user_from = models.ForeignKey(
        CustomUser, related_name="rel_from_set", on_delete=models.CASCADE
    )
    user_to = models.ForeignKey(
        CustomUser, related_name="rel_to_set", on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return f"{self.user_from.email} follows {self.user_to.email}"


class EmailVerification(BaseAbstractModel):
    """Model that represent a mail sent to a user for email verification."""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    internal_tracker_id = models.UUIDField(default=uuid.uuid4)
    is_active = models.BooleanField(default=True)
    expiration_date = models.DateTimeField()


class PasswordResetAttempt(BaseAbstractModel):
    """Model that represent an attempt to reset a users password."""

    STATUS_PENDING = 0  # otp has been created and sent to users email
    STATUS_OTP_VERIFIED = 1  # otp has been verified and password can be reset
    STATUS_SUCCESS = 2  # password has been successfully changed
    STATUS_EXPIRED = 3  # otp has expired

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_OTP_VERIFIED, "Verified"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_EXPIRED, "Expired"),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    internal_tracker_id = models.UUIDField(default=uuid.uuid4)
    signed_otp = models.TextField()
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_PENDING)
    expiration_datetime = models.DateTimeField()

    def generate_signed_identifier(self) -> str:
        """Generate a signed value containg the id of a record."""
        signer = signing.TimestampSigner()
        return signer.sign(value=self.id)


class FriendShipInvitation(BaseAbstractModel):
    INVITATION_STATUS_PENDING = 0
    INVITATION_STATUS_ACCEPTED = 1
    INVITATION_STATUS_REJECTED = 2
    INVITATION_STATUS_CANCLED = 3

    INVITATION_STATUS_CHOICES = (
        (INVITATION_STATUS_PENDING, "Pending"),
        (INVITATION_STATUS_ACCEPTED, "Accepted"),
        (INVITATION_STATUS_REJECTED, "Rejected"),
        (INVITATION_STATUS_CANCLED, "Cancled"),
    )

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="friendship_invitations"
    )
    status = models.IntegerField(
        choices=INVITATION_STATUS_CHOICES, default=INVITATION_STATUS_PENDING
    )
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="friendship_invitation_set"
    )


class FriendShip(BaseAbstractModel):
    users = models.ManyToManyField(
        CustomUser,
        through="accounts.UserFriendShipSettings",
    )


class UserFriendShipSettings(BaseAbstractModel):
    """Model to allow user control over friendship."""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    friendship = models.ForeignKey(FriendShip, on_delete=models.CASCADE)
    invitation = models.ForeignKey(
        "accounts.FriendShipInvitation", on_delete=models.CASCADE
    )
    is_blocked = models.BooleanField(default=False)


class UserGenericSettings(BaseAbstractModel):
    user = models.OneToOneField(
        to=CustomUser, related_name="settings", on_delete=models.CASCADE
    )
    notification = models.JSONField(
        encoder=DjangoJSONEncoder,
        validators=[validate_settings_notification],
    )

    def __str__(self) -> str:
        return f"{self.user.id}_settings"
