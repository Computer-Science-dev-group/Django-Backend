# Generated by Django 4.0.10 on 2023-05-05 22:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uia_backend.accounts.models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomUser",
            fields=[
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "created_datetime",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                (
                    "updated_datetime",
                    models.DateTimeField(auto_now=True, verbose_name="Last update at"),
                ),
                ("first_name", models.CharField(max_length=150)),
                ("last_name", models.CharField(max_length=150)),
                ("display_name", models.CharField(max_length=150)),
                (
                    "email",
                    models.EmailField(
                        max_length=255, unique=True, verbose_name="email address"
                    ),
                ),
                ("password", models.CharField(max_length=128)),
                (
                    "profile_picture",
                    models.ImageField(
                        null=True,
                        upload_to=uia_backend.accounts.models.user_profile_upload_location,
                    ),
                ),
                (
                    "cover_photo",
                    models.ImageField(
                        null=True,
                        upload_to=uia_backend.accounts.models.user_cover_profile_upload_location,
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                ("bio", models.TextField(blank=True, null=True)),
                ("gender", models.CharField(blank=True, max_length=10, null=True)),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                ("faculty", models.CharField(max_length=60)),
                ("department", models.CharField(max_length=60)),
                ("year_of_graduation", models.CharField(max_length=4)),
                ("is_active", models.BooleanField(default=False)),
                ("is_verified", models.BooleanField(default=False)),
                ("last_login", models.DateTimeField(null=True)),
                (
                    "app_version",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="EmailVerification",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "created_datetime",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                (
                    "updated_datetime",
                    models.DateTimeField(auto_now=True, verbose_name="Last update at"),
                ),
                ("internal_tracker_id", models.UUIDField(default=uuid.uuid4)),
                ("is_active", models.BooleanField(default=True)),
                ("expiration_date", models.DateTimeField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
