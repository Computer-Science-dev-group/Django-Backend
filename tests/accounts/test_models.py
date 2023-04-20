from django.test import TestCase
from factory.django import DjangoModelFactory
import uuid

from uia_backend.accounts.models import (
    CustomUser,
    user_cover_profile_upload_location,
    user_profile_upload_location,
)


class UserModelFactory(DjangoModelFactory):
    email = "user@example.com"
    first_name = "John"
    last_name = "Doe"
    display_name = "JohnDoe"
    faculty = "Science"
    department = "Computer Science"
    year_of_graduation = "2019"
    password = "f_g68Ata7jPqqmm"

    class Meta:
        model = CustomUser


class UserTests(TestCase):
    def test_unicode(self):
        user = UserModelFactory.create()
        self.assertEqual(str(user), user.email)


class UserManagerTests(TestCase):
    def test_create_user_successful(self):
        user = CustomUser.objects.create_user(
            email="user@example.com", password="f_g68Ata7jPqqmm"
        )

        self.assertTrue(isinstance(user, CustomUser))

    def test_create_user_with_no_email(self):
        """Test to assert that creating a user failes if email is a nullable."""

        self.assertRaises(
            ValueError,
            CustomUser.objects.create_user,
            email=None,
            password="f_g68Ata7jPqqmm",
        )


class UserProfileUploadLocation(TestCase):
    def test_method(self):
        user = UserModelFactory.create()
        file_name = "profile.png"
        expected_output = f"users/{user.id}/profile/{file_name}"
        self.assertEqual(
            user_profile_upload_location(instance=user, filename=file_name),
            expected_output,
        )


class UserCoverProfileUploadLocation(TestCase):
    def test_method(self):
        user = UserModelFactory.create()
        file_name = "cover.png"
        expected_output = f"users/{user.id}/cover/{file_name}"
        self.assertEqual(
            user_cover_profile_upload_location(instance=user, filename=file_name),
            expected_output,
        )
