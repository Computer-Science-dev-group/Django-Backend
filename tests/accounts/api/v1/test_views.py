from unittest import mock

from django.core import signing
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from tests.accounts.test_models import EmailVerificationFactory, UserModelFactory
from uia_backend.accounts import constants
from uia_backend.accounts.api.v1.serializers import VerifyOTPSerializer
from uia_backend.accounts.models import OTP, CustomUser


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
            "first_name": "John",
            "last_name": "Doe",
            "email": "johndoe@example.com",
            "faculty": "Engineering",
            "department": "Computer Science",
            "year_of_graduation": "2022",
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


class ForgotPasswordAPIViewTestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(
            email="test@example.com", password="testpassword"
        )

    def test_post_with_valid_data(self):
        url = reverse("accounts_api_v1:forget_password")
        data = {"email": self.user.email}

        @mock.patch("uia_backend.accounts.utils.send_user_forget_password_mail")
        def test_forget_password_api(self, mock_send_mail):
            response = self.client.post(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_send_mail.assert_called_once(self.user, None, None)


class VerifyOTPViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("accounts_api_v1:verify_otp")
        self.user = CustomUser.objects.create_user(
            email="testuser@example.com", password="testpassword"
        )
        # To prevent 401 errors
        self.client.force_authenticate(user=self.user)

        self.expiry_time = timezone.now() + timezone.timedelta(
            minutes=constants.OTP_ACTIVE_PERIOD
        )
        self.otp = OTP.objects.create(
            user=self.user, otp="1234", expiry_time=self.expiry_time
        )

    def test_valid_post_request(self):
        """
        Test for valid post request with correct data
        """
        data = {
            "email": self.user.email,
            "otp": self.otp.otp,
            "new_password": "newpassword",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data, {"detail": "Password has been reset successfully."}
        )
        # self.assertTrue(Token.objects.get(user=self.user))

    def test_invalid_post_request(self):
        """
        Test for invalid post request with incorrect data
        """
        data = {
            "email": "nonexistent@example.com",
            "otp": self.otp.otp,
            "new_password": "newpassword",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {"email": ["No user with this email address exists."]}
        )

    def test_invalid_otp(self):
        """
        Test for invalid OTP
        """
        data = {"email": self.user.email, "otp": "4321", "new_password": "newpassword"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"non_field_errors": ["Invalid OTP."]})

    def test_expired_otp(self):
        """
        Test for expired OTP
        """
        expiry_time = timezone.now() - timezone.timedelta(minutes=5)
        self.otp.expiry_time = expiry_time
        self.otp.save()
        data = {
            "email": self.user.email,
            "otp": self.otp.otp,
            "new_password": "newpassword",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"non_field_errors": ["OTP has expired."]})

    def test_missing_email_field(self):
        """
        Test for missing email field
        """
        data = {"otp": "123456", "new_password": "newpassword"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"email": ["This field is required."]})

    def test_missing_otp_field(self):
        """
        Test for missing OTP field
        """
        data = {"email": self.user.email, "new_password": "newpassword"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"otp": ["This field is required."]})

    def test_post_with_invalid_serializer(self):
        data = {
            "email": "testuser@example.com",
            "otp": "1234",
            "new_password": "newpassword123",
        }
        serializer = VerifyOTPSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Invalidate the serializer by removing the required "new_password" field
        data.pop("new_password")
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
