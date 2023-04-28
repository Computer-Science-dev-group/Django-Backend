import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from uia_backend.libs.base_models import BaseAbstractModel


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


class CustomUser(BaseAbstractModel, AbstractBaseUser):
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

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "faculty",
        "department",
        "year_of_graduation",
    ]

    def __str__(self):
        return self.email


class EmailVerification(BaseAbstractModel):
    """Model that represent a mail sent to a user for email verification."""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    internal_tracker_id = models.UUIDField(default=uuid.uuid4)
    is_active = models.BooleanField(default=True)
    expiration_date = models.DateTimeField()


# OTP Verification
class OTP(BaseAbstractModel):
    """
    Model that generates the OTP
    """

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=10)
    is_active = models.BooleanField(default=False)
    expiry_time = models.DateTimeField()
