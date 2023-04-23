from unittest import mock

from django.core import signing
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from tests.accounts.test_models import EmailVerificationFactory, UserModelFactory
from uia_backend.accounts.models import CustomUser


class UserRegistrationAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("accounts_api_v1:user_registration")

    @mock.patch("uia_backend.notification.tasks.send_template_email_task.delay")
    def test_user_registration_valid_data_successful(self, mock_send_email_task):
        """
        Test that user registration with valid data is successful.
        """

        # Create mock user data
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "johndoe@example.com",
            "password": "f_g68Ata7jPqqmm",
            "faculty": "Engineering",
            "department": "Computer Science",
            "year_of_graduation": "2022",
        }

        response = self.client.post(path=self.url, data=user_data)
        self.assertEqual(response.status_code, 201)

        expected_response_data = {
            "info": "Success",
            "message": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "johndoe@example.com",
                "faculty": "Engineering",
                "department": "Computer Science",
                "year_of_graduation": "2022",
            },
        }

        self.assertDictEqual(expected_response_data, response.data)

        user = CustomUser.objects.filter(
            email=user_data["email"], is_active=False
        ).first()
        self.assertIsNotNone(user)

        self.assertNotEqual(user.password, user_data["password"])
        self.assertTrue(user.check_password(user_data["password"]))
        mock_send_email_task.assert_called_once()

    def test_user_registration_email_already_exists(self):
        """Test user registration fails with code 400 if user data already exits."""

        user = UserModelFactory.create()

        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": user.email,
            "password": "password123",
            "faculty": "Engineering",
            "department": "Computer Science",
            "year_of_graduation": "2022",
        }

        response = self.client.post(path=self.url, data=user_data)

        expected_response_data = {
            "info": "Failure",
            "message": "custom user with this email address already exists.",
        }
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, expected_response_data)


class EmailVerificationAPIViewTests(APITestCase):
    def setUp(self):
        self.user = UserModelFactory.create(is_active=False)
        self.email_verification = EmailVerificationFactory.create(
            user=self.user,
            is_active=True,
            expiration_date=timezone.now(),
        )

        signer = signing.TimestampSigner()
        signature = signer.sign_object(str(self.email_verification.id))

        self.url = reverse("accounts_api_v1:email_verification", args=[signature])

    def test_email_verification_successful(self):
        """Test if signature is valid then account is successfully verified."""

        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 200)

        self.email_verification.refresh_from_db()
        self.user.refresh_from_db()

        self.assertTrue(self.user.is_active)
        self.assertFalse(self.email_verification.is_active)

        self.assertDictEqual(
            response.data,
            {
                "info": "Success",
                "message": "Your account has been successfully verified.",
            },
        )

    def test_email_verification_failed_invalid_signature(self):
        """Test that view handles invalid signature properly."""

        signature = "snsjahskjhsjkahskahsklhaksjhkas"
        self.url = reverse("accounts_api_v1:email_verification", args=[signature])

        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 400)

        self.email_verification.refresh_from_db()
        self.user.refresh_from_db()

        self.assertFalse(self.user.is_active)
        self.assertTrue(self.email_verification.is_active)

        self.assertDictEqual(
            response.data,
            {
                "info": "Failure",
                "message": "Invalid link or link has expired.",
            },
        )


class UserProfileAPIViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts_api_v1:user_profile")
        self.user = UserModelFactory.create(is_active=True, is_verified=True)

    def test_unauthenticated_user_can_view_profile(self):
        """Test if an unauthenticated user can view profile."""

        response = self.client.get(self.url, args=[self.user.id])
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_view_profile(self):
        """Test if an authenticated user can view profile."""

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, args=[self.user.id])
        self.assertEqual(response.status_code, 200)

    def test_if_authenticated_user_can_update_profile(self):
        """Test if an authenticated user can update profile."""

        user_data = {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "password": self.user.password,
            "faculty": self.user.faculty,
            "department": self.user.department,
            "bio": "Hi, I am a graduate of Computer Science, UI",
            "gender": "Male",
            "display_name": "John Peters",
            "phone_number": "08020444345",
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.put(path=self.url, data=user_data)

        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.data,
            {
                "info": "Success",
                "message": "Your profile has been successfully updated.",
            },
        )

    def test_if_unauthenticated_user_can_update_profile(self):
        """Test if an unauthenticated user can update profile."""

        user_data = {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "password": self.user.password,
            "faculty": self.user.faculty,
            "department": self.user.department,
            "bio": "Hi, I am a graduate of Computer Science, UI",
            "gender": "Male",
            "display_name": "John Peters",
            "phone_number": "08020444345",
        }

        response = self.client.put(path=self.url, data=user_data)

        self.assertEqual(response.status_code, 401)

        self.assertDictEqual(
            response.data,
            {
                "info": "Failure",
                "message": "Authentication credentials were not provided.",
            },
        )


# NOTE: Joseph Complete this test when Abdulahhi's UserLogin PR is merged
class ChangePasswordAPIViewTests(APITestCase):
    def setUp(self):
        self.user = UserModelFactory.create(is_active=False)
