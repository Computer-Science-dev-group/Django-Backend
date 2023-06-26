import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core import signing
from django.db import models
from django.core.exceptions import ValidationError
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
    follows = models.ManyToManyField("self", symmetrical=False, related_name="followers", through="Follows")
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

    def follow(self, user):
        """Create a follow relationship between two users"""
        follow, created = Follows.objects.get_or_create(user_from=self, user_to=user)
        return created

    def unfollow(self, user):
        """Remove a follow relationship between two users"""
        Follows.objects.filter(user_from=self, user_to=user).delete()

    def is_following(self, user):
        """Check if self is following user"""
        return Follows.objects.filter(user_from=self, user_to=user).exists()

    def get_followers(self):
        """Get the followers of self"""
        return CustomUser.objects.filter(follows__user_to=self)

    def get_followers_count(self):
        """Get the followers of self count"""
        return CustomUser.objects.filter(follows__user_to=self).count()

    def get_following(self):
        """Get the users followed by self"""
        return CustomUser.objects.filter(followers__user_from=self)

    def get_following_count(self):
        """Get the users followed by self"""
        return CustomUser.objects.filter(followers__user_from=self).count()


class Follows(models.Model):
    user_from = models.ForeignKey(CustomUser, related_name="rel_from_set", on_delete=models.CASCADE)
    user_to = models.ForeignKey(CustomUser, related_name="rel_to_set", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["-created"]),
        ]
        ordering = ["-created"]

    def __str__(self):
        return f"{self.user_from} follows {self.user_to}"


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
