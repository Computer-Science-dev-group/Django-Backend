import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..constants.users import DEPARTMENT_CHOICES, FACULTY_CHOICES
from ..utils.validators import validate_password


class CustomUserManager(BaseUserManager):
    """ Custom User Manager for UIA User Model """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser):
    """ Custom User model for UIA """

    id = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, editable=False, primary_key=True
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    display_name = models.CharField(max_length=150)
    email = models.EmailField(verbose_name='email address',
                              max_length=255, unique=True)
    password = models.CharField(max_length=128, validators=[validate_password])
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    cover_photo = models.ImageField(upload_to='cover_photos', blank=True, null=True)
    phone_number = models.CharField(max_length=65, null=True)
    bio = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    links = models.ManyToManyField(to='Link', blank=True)
    faculty_or_college = models.CharField(max_length=60, choices=FACULTY_CHOICES)
    department = models.CharField(max_length=65, choices=DEPARTMENT_CHOICES)
    year_of_graduation = models.CharField(max_length=4)
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(_("Last login time"), auto_now=True)
    app_version = models.CharField(max_length=100, blank=True, null=True)

    created_datetime = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_datetime = models.DateTimeField(_("Last update at"), auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'faculty_or_college', 'department', 'year_of_graduation']

    class Meta:
        ordering = ['-created_datetime']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['first_name'], name='first_name_idx'),
        ]
        unique_together = ['id', 'year_of_graduation', 'faculty_or_college', 'department']

    def __str__(self):
        return self.email

    def full_name(self):
        return f'{self.first_name} {self.last_name}'


class Link(models.Model):
    url = models.URLField(null=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.title}'
