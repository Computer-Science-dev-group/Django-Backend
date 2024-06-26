from datetime import timedelta
from unittest import mock
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

import responses
from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from tests.accounts.test_models import (
    EmailVerificationFactory,
    FollowsFactory,
    FriendShipFactory,
    FriendShipInvitationFactory,
    PasswordResetAttemptFactory,
    UserFriendShipSettingsFactory,
    UserGenericSettingsFactory,
    UserModelFactory,
)
from uia_backend.accounts.api.v1.serializers import (
    FollowingSerializer,
    ProfileSerializer,
    UserProfileSerializer,
)
from uia_backend.accounts.constants import (
    PASSWORD_RESET_ACTIVE_PERIOD,
    PASSWORD_RESET_TEMPLATE_ID,
)
from uia_backend.accounts.models import (
    CustomUser,
    Follows,
    FriendShip,
    FriendShipInvitation,
    PasswordResetAttempt,
    UserFriendShipSettings,
)
from uia_backend.cluster.models import Cluster, ClusterMembership, InternalCluster
from uia_backend.libs.testutils import get_test_image_file
from uia_backend.notification.constants import (
    FOLLOW_USER_NOTIFICATION,
    UNFOLLOW_USER_NOTIFICATION,
)


class UserRegistrationAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("accounts_api_v1:user_registration")

    @mock.patch("uia_backend.accounts.tasks.setup_user_profile_task.delay")
    @mock.patch("uia_backend.notification.tasks.send_template_email_task.delay")
    def test_user_registration_valid_data_successful(
        self, mock_send_email_task, mock_setup_profile_task
    ):
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
            "status": "Success",
            "code": 201,
            "data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "johndoe@example.com",
                "faculty": "Engineering",
                "department": "Computer Science",
                "year_of_graduation": "2022",
            },
        }

        self.assertDictEqual(expected_response_data, response.json())

        user = CustomUser.objects.filter(
            email=user_data["email"], is_active=False
        ).first()
        self.assertIsNotNone(user)

        self.assertNotEqual(user.password, user_data["password"])
        self.assertTrue(user.check_password(user_data["password"]))
        mock_send_email_task.assert_called_once()
        mock_setup_profile_task.assert_called_once_with(user_id=user.id)

    def test_user_registration_email_already_exists(self):
        """Test user registration fails with code 400 if user data already exits."""

        user = UserModelFactory.create()

        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": user.email,
            "password": "asasi'jidjdj;osd",
            "faculty": "Engineering",
            "department": "Computer Science",
            "year_of_graduation": "2022",
        }

        response = self.client.post(path=self.url, data=user_data)

        expected_response_data = {
            "status": "Error",
            "code": 400,
            "data": {
                "email": ["custom user with this email address already exists."],
            },
        }
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), expected_response_data)


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

    def test__add_user_to_defualt_clusters_on_successful_email_verification(self):
        """Test to ensure that user is added to default clusters on email verification."""
        response = self.client.get(path=self.url)
        # TEST

        # Show that verification was sucessful
        self.assertEqual(response.status_code, 200)

        # Show that user was has been added to all default clusters
        self.assertEqual(InternalCluster.objects.all().count(), 4)
        self.assertEqual(Cluster.objects.all().count(), 4)
        self.assertEqual(ClusterMembership.objects.filter(user=self.user).count(), 4)

        global_cluster = InternalCluster.objects.filter(
            name="global", description=""
        ).first()
        self.assertIsNotNone(global_cluster)
        self.assertIsNotNone(global_cluster.cluster)
        self.assertTrue(
            ClusterMembership.objects.filter(
                user=self.user, cluster=global_cluster.cluster
            ).exists()
        )

        faculty_cluster = InternalCluster.objects.filter(
            name=f"faculty of {self.user.faculty}", description=""
        ).first()
        self.assertIsNotNone(faculty_cluster)
        self.assertIsNotNone(faculty_cluster.cluster)
        self.assertTrue(
            ClusterMembership.objects.filter(
                user=self.user, cluster=faculty_cluster.cluster
            ).exists()
        )

        department_cluster = InternalCluster.objects.filter(
            name=f"{self.user.department} department", description=""
        ).first()
        self.assertIsNotNone(department_cluster)
        self.assertIsNotNone(department_cluster.cluster)
        self.assertTrue(
            ClusterMembership.objects.filter(
                user=self.user, cluster=department_cluster.cluster
            ).exists()
        )

        yog_cluster = InternalCluster.objects.filter(
            name=f"{self.user.year_of_graduation} set", description=""
        ).first()
        self.assertIsNotNone(yog_cluster)
        self.assertIsNotNone(yog_cluster.cluster)
        self.assertTrue(
            ClusterMembership.objects.filter(
                user=self.user, cluster=yog_cluster.cluster
            ).exists()
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


class UserProfileAPIViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts_api_v1:user_profile")
        self.user = UserModelFactory.create(is_active=True, is_verified=True)

    def test_unauthenticated_user_cant_view_profile(self):
        """Test if an unauthenticated user can view profile."""

        response = self.client.get(self.url, args=[self.user.id])
        self.assertEqual(response.status_code, 401)

        self.assertDictEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_unauthenticated_user_cant_update_profile(self):
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
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_authenticated_user_can_view_profile(self):
        """Test if an authenticated user can view profile."""

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.maxDiff = None
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.user.id),
                    "first_name": self.user.first_name,
                    "last_name": self.user.last_name,
                    "profile_picture": None,
                    "cover_photo": None,
                    "faculty": self.user.faculty,
                    "department": self.user.department,
                    "year_of_graduation": self.user.year_of_graduation,
                    "bio": self.user.bio,
                    "gender": self.user.gender,
                    "display_name": f"@{self.user.display_name.lower()}",
                    "phone_number": self.user.phone_number,
                    "date_of_birth": self.user.date_of_birth.isoformat(),
                    "follower_count": 0,
                    "following_count": 0,
                    "ws_channel_name": f"$users:{self.user.id}#{self.user.id}",
                },
            },
        )

    def test_if_authenticated_user_can_update_profile(self):
        """Test if an authenticated user can update profile."""

        user_data = {
            "first_name": "Sapa",
            "last_name": "Lord",
            "cover_photo": get_test_image_file(),
            "profile_picture": get_test_image_file(),
            "bio": "Hi, I am a graduate of Computer Science, UI",
            "gender": "Male",
            "display_name": "_Nickel_12",
            "phone_number": "08020444345",
            "date_of_birth": timezone.now().date().isoformat(),
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.put(path=self.url, data=user_data, format="multipart")
        self.maxDiff = None
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.user.id),
                    "first_name": "Sapa",
                    "last_name": "Lord",
                    "faculty": self.user.faculty,
                    "department": self.user.department,
                    "bio": user_data["bio"],
                    "gender": user_data["gender"],
                    "display_name": "@_nickel_12",
                    "phone_number": user_data["phone_number"],
                    "date_of_birth": user_data["date_of_birth"],
                    "cover_photo": f"http://testserver/media/users/{self.user.id}/cover/image.png",
                    "profile_picture": f"http://testserver/media/users/{self.user.id}/profile/image.png",
                    "year_of_graduation": self.user.year_of_graduation,
                    "follower_count": 0,
                    "following_count": 0,
                    "ws_channel_name": f"$users:{self.user.id}#{self.user.id}",
                },
            },
        )

        # check that changes are reflected in the DB
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Sapa")
        self.assertEqual(self.user.last_name, "Lord")
        self.assertEqual(self.user.bio, "Hi, I am a graduate of Computer Science, UI")
        self.assertEqual(self.user.gender, "Male")
        self.assertEqual(self.user.display_name, "_nickel_12")
        self.assertEqual(self.user.phone_number, "08020444345")
        self.assertEqual(self.user.date_of_birth, timezone.now().date())


class ChangePasswordAPIViewTests(APITestCase):
    def setUp(self):
        self.user = UserModelFactory.create(is_active=True)
        self.url = reverse("accounts_api_v1:change_password")
        self.auth_headers = f"Bearer {AccessToken.for_user(self.user)}"

    @responses.activate
    @mock.patch("uia_backend.notification.tasks.send_template_email_task.delay")
    def test_change_password_authenticated_user_successful(self, mock_send_email_task):
        """Test change password successful for authenticated user."""

        responses.add(
            responses.GET,
            f"{settings.IP_API_CO_URL}/127.0.0.1/region/",
            body="Region",
            status=200,
        )

        valid_data = {"password": "f_g68Ata7jPqqmm"}

        self.client.credentials(
            HTTP_AUTHORIZATION=self.auth_headers,
            HTTP_USER_AGENT="Mozilla/5.0",
            REMOTE_ADDR="127.0.0.1",
        )
        response = self.client.put(
            data=valid_data,
            path=self.url,
        )

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {"message": "Password Changed Successfully."},
            },
        )
        mock_send_email_task.assert_called_once()

    def test_change_password_unauthenticated_user(self):
        """Test change password failed for unauthenticated user."""

        valid_data = {"password": "f_g68Ata7jPqqmm"}

        response = self.client.put(data=valid_data, path=self.url)

        self.assertEqual(response.status_code, 401)
        self.assertDictEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_change_password_invalid_password(self):
        """Test change password failed for invalid password."""

        valid_data = {"password": "string"}

        self.client.credentials(HTTP_AUTHORIZATION=self.auth_headers)

        response = self.client.put(
            data=valid_data,
            path=self.url,
        )

        self.assertEqual(response.status_code, 400)


class LoginAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(is_active=True, email="user@example.com")
        self.user.set_password("string")
        self.user.save()
        self.url = reverse("accounts_api_v1:user_signin")

    def test_successful_login(self):
        """Test user logs in successfully."""

        valid_data = {"email": "user@example.com", "password": "string"}

        refresh_token_mock = MagicMock()
        refresh_token_mock.__str__ = lambda self: "refresh_token"
        refresh_token_mock.access_token.__str__ = lambda self: "access_token"

        with (
            mock.patch(
                "rest_framework_simplejwt.tokens.RefreshToken.for_user",
                side_effect=[refresh_token_mock],
            ) as jwt_token_mock,
            mock.patch(
                "uia_backend.accounts.api.v1.serializers.generate_centrifugo_connection_token",
                side_effect=["ws_token"],
            ) as mock_generate_cent_token,
        ):
            response = self.client.post(data=valid_data, path=self.url)
        self.maxDiff = None
        mock_generate_cent_token.assert_called_once()
        jwt_token_mock.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "auth_token": "access_token",
                    "refresh_token": "refresh_token",
                    "ws_token": "ws_token",
                    "profile": dict(
                        UserProfileSerializer().to_representation(instance=self.user)
                    ),
                },
            },
        )

    def test_invalid_credentials_email(self):
        """Test login with invalid email fails."""
        valid_data = {"email": "invalid@example.com", "password": "string"}

        response = self.client.post(data=valid_data, path=self.url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "non_field_errors": [
                        "Invalid credentials or your account is inactive."
                    ]
                },
            },
        )

    def test_invalid_credentials_password(self):
        """Test login with invalid password fails."""
        valid_data = {"email": "user@example.com", "password": "wrong"}

        response = self.client.post(data=valid_data, path=self.url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "non_field_errors": [
                        "Invalid credentials or your account is inactive."
                    ]
                },
            },
        )

    def test_inactive_user(self):
        """Test login failes when user is inactive."""
        self.user.is_active = False
        self.user.save()

        valid_data = {"email": "user@example.com", "password": "string"}

        response = self.client.post(data=valid_data, path=self.url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "non_field_errors": [
                        "Invalid credentials or your account is inactive."
                    ]
                },
            },
        )


class ResetPasswordRequestAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com", is_active=True)
        self.url = reverse("accounts_api_v1:request_password_reset_otp")

    @mock.patch(
        "uia_backend.accounts.api.v1.views.PasswordRestThrottle.allow_request",
        side_effect=[True],
    )
    @mock.patch("uia_backend.accounts.utils.send_template_email_task")
    def test_valid_email_provided(self, mock_send_email_task, mock_throttle):
        """Test that a valid email address is provided and OTP is successfully sent."""

        with mock.patch(
            "uia_backend.accounts.api.v1.serializers.generate_reset_password_otp",
            side_effect=[("000000", "")],
        ):
            response = self.client.post(self.url, {"email": self.user.email})

        self.assertEqual(response.status_code, 201)
        self.assertDictEqual(
            response.json(),
            {
                "status": "Success",
                "code": 201,
                "data": {"message": "OTP has been sent to this email address."},
            },
        )
        self.assertTrue(
            PasswordResetAttempt.objects.filter(
                user=self.user, status=PasswordResetAttempt.STATUS_PENDING
            ).exists()
        )

        reset_record = PasswordResetAttempt.objects.filter(
            user=self.user, status=PasswordResetAttempt.STATUS_PENDING
        ).first()

        mock_send_email_task.assert_called_once_with(
            recipients=[self.user.email],
            internal_tracker_ids=[str(reset_record.internal_tracker_id)],
            template_id=PASSWORD_RESET_TEMPLATE_ID,
            template_merge_data={
                self.user.email: {
                    "otp": "000000",
                    "expiration_in_minutes": PASSWORD_RESET_ACTIVE_PERIOD,
                },
            },
        )

    @mock.patch(
        "uia_backend.accounts.api.v1.views.PasswordRestThrottle.allow_request",
        side_effect=[True],
    )
    def test_invalid_email_provided(self, mock_throttle):
        """Test that an invalid email address is provided and appropriate error message is returned."""
        email = "unkwown"

        response = self.client.post(self.url, {"email": email})

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {"email": ["Enter a valid email address."]},
            },
        )
        self.assertFalse(
            PasswordResetAttempt.objects.filter(
                user=self.user, status=PasswordResetAttempt.STATUS_PENDING
            ).exists()
        )

    @mock.patch(
        "uia_backend.accounts.api.v1.views.PasswordRestThrottle.allow_request",
        side_effect=[True],
    )
    def test_inactive_user_email_provided(self, mock_throttle):
        """Test that an email address of an inactive user is provided and appropriate error message is returned."""
        user = CustomUser.objects.create(email="test@example.com", is_active=False)
        response = self.client.post(self.url, {"email": user.email})

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "email": [
                        "Invalid email address. No active user with this credentials was found."
                    ]
                },
            },
        )
        self.assertFalse(
            PasswordResetAttempt.objects.filter(
                user=self.user, status=PasswordResetAttempt.STATUS_PENDING
            ).exists()
        )


class VerifyResetPasswordAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com", is_active=True)
        self.otp = "000000"
        self.reset_record = PasswordResetAttemptFactory.create(
            status=PasswordResetAttempt.STATUS_PENDING,
            signed_otp=signing.Signer().sign(self.otp),
            expiration_datetime=timezone.now() + timedelta(hours=2),
            user=self.user,
        )
        self.url = reverse("accounts_api_v1:verify_password_reset_otp")

    def test_verify_otp_successfully(self):
        """Test verifying otp is successful."""

        request_data = {"otp": self.otp, "email": self.user.email}
        response = self.client.post(path=self.url, data=request_data)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "password_change_key": self.reset_record.generate_signed_identifier()
                },
            },
        )

        self.reset_record.refresh_from_db()
        self.assertEqual(
            self.reset_record.status, PasswordResetAttempt.STATUS_OTP_VERIFIED
        )

    def test_verify_otp_fails_when_otp_is_invaild(self):
        """Test that view fails when otp is invalid."""

        request_data = {"otp": "111111", "email": self.user.email}
        response = self.client.post(path=self.url, data=request_data)

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {"otp": ["Invalid otp or otp has expired."]},
            },
        )

        self.reset_record.refresh_from_db()
        self.assertEqual(self.reset_record.status, PasswordResetAttempt.STATUS_PENDING)

    def test_verify_otp_fails_when_reset_record_status_is_not_pending(self):
        """Test that view fails when PasswordResetAttempt status is not pending."""

        self.reset_record.status = PasswordResetAttempt.STATUS_EXPIRED
        self.reset_record.save()

        request_data = {"otp": self.otp, "email": self.user.email}
        response = self.client.post(path=self.url, data=request_data)

        self.assertEqual(response.status_code, 400)

        self.assertDictEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {"otp": ["Invalid otp or otp has expired."]},
            },
        )

        self.reset_record.refresh_from_db()
        self.assertEqual(self.reset_record.status, PasswordResetAttempt.STATUS_EXPIRED)

    def test_verify_otp_fails_when_reset_record_has_expired(self):
        """Test that view fails when PasswordResetAttempt has expired."""

        self.reset_record.expiration_datetime = timezone.now() - timedelta(minutes=1)
        self.reset_record.save()

        request_data = {"otp": self.otp, "email": self.user.email}
        response = self.client.post(path=self.url, data=request_data)

        request_data = {"otp": self.otp, "email": self.user.email}
        response = self.client.post(path=self.url, data=request_data)

        self.assertEqual(response.status_code, 400)

        self.assertDictEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {"otp": ["Invalid otp or otp has expired."]},
            },
        )

        self.reset_record.refresh_from_db()
        self.assertEqual(self.reset_record.status, PasswordResetAttempt.STATUS_PENDING)


class ResetPasswordAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com", is_active=True)
        self.otp = "000000"
        self.reset_record = PasswordResetAttemptFactory.create(
            status=PasswordResetAttempt.STATUS_OTP_VERIFIED,
            signed_otp=signing.Signer().sign(self.otp),
            expiration_datetime=timezone.now() + timedelta(hours=2),
            user=self.user,
        )
        self.url = reverse("accounts_api_v1:reset_password")

    def test_reset_password_successfully(self):
        """Test that view allows user to change password successfuly."""

        self.user.set_password("string")
        self.user.save()

        request_data = {
            "password_change_key": self.reset_record.generate_signed_identifier(),
            "new_password": "f_g68Ata7jPqqmm",
            "email": self.user.email,
        }

        response = self.client.post(path=self.url, data=request_data)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {"message": "Password Reset Successfully."},
            },
        )

        self.user.refresh_from_db()
        self.reset_record.refresh_from_db()
        self.assertTrue(self.user.check_password("f_g68Ata7jPqqmm"))
        self.assertEqual(self.reset_record.status, PasswordResetAttempt.STATUS_SUCCESS)

    def test_reset_password_fails_when_new_password_is_weak(self):
        self.user.set_password("string")
        self.user.save()

        request_data = {
            "password_change_key": self.reset_record.generate_signed_identifier(),
            "new_password": "password",
            "email": self.user.email,
        }

        response = self.client.post(path=self.url, data=request_data)

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {"new_password": ["['This password is too common.']"]},
            },
        )

        self.user.refresh_from_db()
        self.reset_record.refresh_from_db()

        self.assertFalse(self.user.check_password("password"))
        self.assertTrue(self.user.check_password("string"))

        self.assertEqual(
            self.reset_record.status, PasswordResetAttempt.STATUS_OTP_VERIFIED
        )

    def test_reset_password_fails_when_otp_has_expired(self):
        self.user.set_password("string")
        self.reset_record.expiration_datetime = timezone.now() - timedelta(minutes=1)
        self.reset_record.save()
        self.user.save()

        request_data = {
            "password_change_key": self.reset_record.generate_signed_identifier(),
            "new_password": "f_g68Ata7jPqqmm",
            "email": self.user.email,
        }

        response = self.client.post(path=self.url, data=request_data)

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "password_change_key": [
                        (
                            "Invalid password_change_key or session has expired. "
                            "Please restart process."
                        )
                    ]
                },
            },
        )

        self.user.refresh_from_db()
        self.reset_record.refresh_from_db()

        self.assertFalse(self.user.check_password("password"))
        self.assertTrue(self.user.check_password("string"))

        self.assertEqual(
            self.reset_record.status, PasswordResetAttempt.STATUS_OTP_VERIFIED
        )

    def test_reset_password_fails_when_password_change_key_has_expired(self):
        self.user.set_password("string")
        self.user.save()

        request_data = {
            "password_change_key": self.reset_record.generate_signed_identifier(),
            "new_password": "f_g68Ata7jPqqmm",
            "email": self.user.email,
        }

        with mock.patch(
            "uia_backend.accounts.models.signing.TimestampSigner.unsign",
            side_effect=[signing.BadSignature],
        ):
            response = self.client.post(path=self.url, data=request_data)

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "password_change_key": [
                        (
                            "Invalid password_change_key or session has expired. "
                            "Please restart process."
                        )
                    ]
                },
            },
        )

        self.user.refresh_from_db()
        self.reset_record.refresh_from_db()

        self.assertFalse(self.user.check_password("password"))
        self.assertTrue(self.user.check_password("string"))

        self.assertEqual(
            self.reset_record.status, PasswordResetAttempt.STATUS_OTP_VERIFIED
        )


class UserProfileDetailAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com", is_active=True)

        self.user_follower_count = Follows.objects.filter(user_to=self.user).count()
        self.user_following_count = Follows.objects.filter(user_from=self.user).count()

        self.url = reverse("accounts_api_v1:accounts_detail", args=[self.user.id])

    def test_unauthenticated_user_cannot_get_their_profile(self):
        """Test to assert that an unauthenticated user cannot get  their profile"""

        response = self.client.get(path=self.url)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_get_their_profile(self):
        """Test an authenticated user can get their profile"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(path=self.url)
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.user.id),
                    "first_name": self.user.first_name,
                    "last_name": self.user.last_name,
                    "profile_picture": self.user.profile_picture or None,
                    "cover_photo": self.user.cover_photo or None,
                    "phone_number": self.user.phone_number or None,
                    "display_name": f"@{self.user.first_name.lower()}{self.user.last_name.lower()}",
                    "year_of_graduation": self.user.year_of_graduation,
                    "department": self.user.department,
                    "faculty": self.user.faculty,
                    "bio": self.user.bio,
                    "gender": self.user.gender,
                    "date_of_birth": str(self.user.date_of_birth),
                    "ws_channel_name": f"${settings.USER_NAMESPACE}:{self.user.id}#{self.user.id}",
                    "follower_count": self.user_follower_count,
                    "following_count": self.user_following_count,
                },
            },
        )


class FriendShipInvitationListAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("accounts_api_v1:friendship_invitation")
        self.authenticated_user = UserModelFactory.create(email="user@1example.com")
        self.invited_user = UserModelFactory.create(email="user@2example.com")

    def test_create_invitation_successfuly(self):
        """Test to assert that user can sucessfully create friendship invitations."""

        valid_data = {
            "sent_to": str(self.invited_user.id),
            "status": FriendShipInvitation.INVITATION_STATUS_PENDING,
        }

        self.client.force_authenticate(user=self.authenticated_user)

        response = self.client.post(data=valid_data, path=self.url)

        self.assertEqual(response.status_code, 201)

        invitation_record = FriendShipInvitation.objects.filter(
            created_by=self.authenticated_user,
            user=self.invited_user,
            status=FriendShipInvitation.INVITATION_STATUS_PENDING,
        ).first()

        self.assertIsNotNone(invitation_record)

        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 201,
                "data": {
                    "id": str(invitation_record.id),
                    "sent_to": str(self.invited_user.id),
                    "status": FriendShipInvitation.INVITATION_STATUS_PENDING,
                    "created_by": str(self.authenticated_user.id),
                    "created_datetime": serializers.DateTimeField().to_representation(
                        invitation_record.created_datetime
                    ),
                    "updated_datetime": serializers.DateTimeField().to_representation(
                        invitation_record.updated_datetime
                    ),
                },
            },
        )

    def test_create_invitation_failed_case_1(self):
        """Test to assert that view fails when user tries to send invitation to friend."""

        # Ensure users are friends
        friendship_record = FriendShipFactory.create()
        invitation_record = FriendShipInvitationFactory.create(
            user=self.invited_user,
            status=FriendShipInvitation.INVITATION_STATUS_ACCEPTED,
            created_by=self.authenticated_user,
        )
        UserFriendShipSettingsFactory.create(
            user=self.invited_user,
            friendship=friendship_record,
            invitation=invitation_record,
        )
        UserFriendShipSettingsFactory.create(
            user=self.authenticated_user,
            friendship=friendship_record,
            invitation=invitation_record,
        )

        valid_data = {
            "sent_to": str(self.invited_user.id),
            "status": FriendShipInvitation.INVITATION_STATUS_PENDING,
        }

        self.client.force_authenticate(user=self.authenticated_user)

        response = self.client.post(data=valid_data, path=self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "sent_to": ["Invalid user. Can not send inivitation to this user."]
                },
            },
        )

    def test_create_invitation_failed_case_2(self):
        """Test to assert that view fails when a user already has a pending invitation to friend."""

        FriendShipInvitationFactory.create(
            user=self.invited_user,
            status=FriendShipInvitation.INVITATION_STATUS_PENDING,
            created_by=self.authenticated_user,
        )

        valid_data = {
            "sent_to": str(self.invited_user.id),
            "status": FriendShipInvitation.INVITATION_STATUS_PENDING,
        }

        self.client.force_authenticate(user=self.authenticated_user)

        response = self.client.post(data=valid_data, path=self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "non_field_errors": [
                        "Can not send new invitation. You already have a pending invitation sent to this user."
                    ]
                },
            },
        )

    def test_create_invitation_failed_case_3(self):
        """Test to ensure that invitation view fails when user tries to send invitation to theirself."""

        valid_data = {
            "sent_to": str(self.authenticated_user.id),
            "status": FriendShipInvitation.INVITATION_STATUS_PENDING,
        }

        self.client.force_authenticate(user=self.authenticated_user)

        response = self.client.post(data=valid_data, path=self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {
                    "sent_to": ["Invalid user. Can not send inivitation to this user."]
                },
            },
        )

    def test_list_invitation_successfully(self):
        """Test listing a users invitation"""

        some_other_user = UserModelFactory.create(email="user@3example.com")

        # invvitation record sent by user
        record_1 = FriendShipInvitationFactory.create(
            user=self.invited_user,
            status=FriendShipInvitation.INVITATION_STATUS_PENDING,
            created_by=self.authenticated_user,
        )

        # invvitation record sent to user
        record_2 = FriendShipInvitationFactory.create(
            user=self.invited_user,
            status=FriendShipInvitation.INVITATION_STATUS_PENDING,
            created_by=self.authenticated_user,
        )

        # invitation that shouldn't be listed
        FriendShipInvitationFactory.create(
            user=self.invited_user,
            status=FriendShipInvitation.INVITATION_STATUS_PENDING,
            created_by=some_other_user,
        )

        self.client.force_authenticate(user=self.authenticated_user)
        response = self.client.get(path=self.url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "count": 2,
                "next": None,
                "previous": None,
                "data": [
                    {
                        "id": str(record_2.id),
                        "sent_to": str(record_2.user.id),
                        "status": FriendShipInvitation.INVITATION_STATUS_PENDING,
                        "created_by": str(record_2.created_by.id),
                        "created_datetime": serializers.DateTimeField().to_representation(
                            record_2.created_datetime
                        ),
                        "updated_datetime": serializers.DateTimeField().to_representation(
                            record_2.updated_datetime
                        ),
                    },
                    {
                        "id": str(record_1.id),
                        "sent_to": str(record_1.user.id),
                        "status": FriendShipInvitation.INVITATION_STATUS_PENDING,
                        "created_by": str(record_1.created_by.id),
                        "created_datetime": serializers.DateTimeField().to_representation(
                            record_1.created_datetime
                        ),
                        "updated_datetime": serializers.DateTimeField().to_representation(
                            record_1.updated_datetime
                        ),
                    },
                ],
            },
        )


class FriendShipInvitationDetailAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.authenticated_user = UserModelFactory.create(email="user@1example.com")
        self.invited_user = UserModelFactory.create(email="user@2example.com")

        self.invitation_record = FriendShipInvitationFactory.create(
            user=self.invited_user,
            status=FriendShipInvitation.INVITATION_STATUS_PENDING,
            created_by=self.authenticated_user,
        )

        self.url = reverse(
            "accounts_api_v1:friendship_invitation_detail",
            args=[str(self.invitation_record.id)],
        )

    def test_accept_invitation_record_successfully(self):
        """"""

        valid_data = {"status": FriendShipInvitation.INVITATION_STATUS_ACCEPTED}
        self.client.force_authenticate(self.invited_user)

        response = self.client.patch(data=valid_data, path=self.url)

        self.assertEqual(response.status_code, 200)

        self.invitation_record.refresh_from_db()
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.invitation_record.id),
                    "sent_to": str(self.invited_user.id),
                    "status": FriendShipInvitation.INVITATION_STATUS_ACCEPTED,
                    "created_by": str(self.authenticated_user.id),
                    "created_datetime": serializers.DateTimeField().to_representation(
                        self.invitation_record.created_datetime
                    ),
                    "updated_datetime": serializers.DateTimeField().to_representation(
                        self.invitation_record.updated_datetime
                    ),
                },
            },
        )

        friendship_record = FriendShip.objects.filter(
            users__in=[self.authenticated_user, self.invited_user]
        ).first()
        self.assertIsNotNone(friendship_record)
        self.assertEqual(
            UserFriendShipSettings.objects.filter(
                invitation=self.invitation_record, friendship=friendship_record
            ).count(),
            2,
        )

    def test_reject_invitation_record_successfully(self):
        """"""
        valid_data = {"status": FriendShipInvitation.INVITATION_STATUS_REJECTED}
        self.client.force_authenticate(self.invited_user)

        response = self.client.patch(data=valid_data, path=self.url)

        self.assertEqual(response.status_code, 200)

        self.invitation_record.refresh_from_db()
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.invitation_record.id),
                    "sent_to": str(self.invited_user.id),
                    "status": FriendShipInvitation.INVITATION_STATUS_REJECTED,
                    "created_by": str(self.authenticated_user.id),
                    "created_datetime": serializers.DateTimeField().to_representation(
                        self.invitation_record.created_datetime
                    ),
                    "updated_datetime": serializers.DateTimeField().to_representation(
                        self.invitation_record.updated_datetime
                    ),
                },
            },
        )

        friendship_record = FriendShip.objects.filter(
            users__in=[self.authenticated_user, self.invited_user]
        ).first()
        self.assertIsNone(friendship_record)
        self.assertEqual(
            UserFriendShipSettings.objects.filter(
                invitation=self.invitation_record,
            ).count(),
            0,
        )

    def test_cancle_invitation_record_successfully(self):
        """"""

        valid_data = {"status": FriendShipInvitation.INVITATION_STATUS_CANCLED}
        self.client.force_authenticate(self.authenticated_user)

        response = self.client.patch(data=valid_data, path=self.url)

        self.assertEqual(response.status_code, 200)

        self.invitation_record.refresh_from_db()
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.invitation_record.id),
                    "sent_to": str(self.invited_user.id),
                    "status": FriendShipInvitation.INVITATION_STATUS_CANCLED,
                    "created_by": str(self.authenticated_user.id),
                    "created_datetime": serializers.DateTimeField().to_representation(
                        self.invitation_record.created_datetime
                    ),
                    "updated_datetime": serializers.DateTimeField().to_representation(
                        self.invitation_record.updated_datetime
                    ),
                },
            },
        )

        friendship_record = FriendShip.objects.filter(
            users__in=[self.authenticated_user, self.invited_user]
        ).first()
        self.assertIsNone(friendship_record)
        self.assertEqual(
            UserFriendShipSettings.objects.filter(
                invitation=self.invitation_record,
            ).count(),
            0,
        )

    def test_to_ensure_that_non_pending_invitation_record_can_not_be_changed(self):
        self.invitation_record.status = FriendShipInvitation.INVITATION_STATUS_ACCEPTED
        self.invitation_record.save()

        # Try changing to pending
        valid_data = {"status": FriendShipInvitation.INVITATION_STATUS_PENDING}
        self.client.force_authenticate(self.invited_user)

        response = self.client.patch(data=valid_data, path=self.url)

        self.assertEqual(response.status_code, 200)

        self.invitation_record.refresh_from_db()
        self.assertEqual(
            self.invitation_record.status,
            FriendShipInvitation.INVITATION_STATUS_ACCEPTED,
        )
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.invitation_record.id),
                    "sent_to": str(self.invited_user.id),
                    "status": FriendShipInvitation.INVITATION_STATUS_ACCEPTED,
                    "created_by": str(self.authenticated_user.id),
                    "created_datetime": serializers.DateTimeField().to_representation(
                        self.invitation_record.created_datetime
                    ),
                    "updated_datetime": serializers.DateTimeField().to_representation(
                        self.invitation_record.updated_datetime
                    ),
                },
            },
        )

        # Try changing to rejected
        valid_data = {"status": FriendShipInvitation.INVITATION_STATUS_REJECTED}
        response = self.client.patch(data=valid_data, path=self.url)

        self.assertEqual(response.status_code, 200)
        self.invitation_record.refresh_from_db()
        self.assertEqual(
            self.invitation_record.status,
            FriendShipInvitation.INVITATION_STATUS_ACCEPTED,
        )
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.invitation_record.id),
                    "sent_to": str(self.invited_user.id),
                    "status": FriendShipInvitation.INVITATION_STATUS_ACCEPTED,
                    "created_by": str(self.authenticated_user.id),
                    "created_datetime": serializers.DateTimeField().to_representation(
                        self.invitation_record.created_datetime
                    ),
                    "updated_datetime": serializers.DateTimeField().to_representation(
                        self.invitation_record.updated_datetime
                    ),
                },
            },
        )

        # try changing to cancled
        valid_data = {"status": FriendShipInvitation.INVITATION_STATUS_CANCLED}
        self.client.force_authenticate(self.authenticated_user)
        response = self.client.patch(data=valid_data, path=self.url)

        self.assertEqual(response.status_code, 200)
        self.invitation_record.refresh_from_db()

        self.assertEqual(
            self.invitation_record.status,
            FriendShipInvitation.INVITATION_STATUS_ACCEPTED,
        )
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.invitation_record.id),
                    "sent_to": str(self.invited_user.id),
                    "status": FriendShipInvitation.INVITATION_STATUS_ACCEPTED,
                    "created_by": str(self.authenticated_user.id),
                    "created_datetime": serializers.DateTimeField().to_representation(
                        self.invitation_record.created_datetime
                    ),
                    "updated_datetime": serializers.DateTimeField().to_representation(
                        self.invitation_record.updated_datetime
                    ),
                },
            },
        )


class UserProfileListAPIViewTests(APITestCase):
    def setUp(self):
        self.user = UserModelFactory.create(is_active=True)
        self.user_2 = UserModelFactory.create(
            is_active=True,
            email="noob@noob.com",
            first_name="Joan",
            last_name="Pike",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("accounts_api_v1:accounts_list")

    def tearDown(self):
        super().tearDown()
        cache.clear()

    def test_unauthenticated_user_can_view_search(self):
        """Test if an unauthenticated user can search."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_view_search(self):
        """Test if an authenticated user can search."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_with_results(self):
        """Test search with results."""
        expected_data = {
            "count": 2,
            "next": None,
            "previous": None,
            "status": "Success",
            "code": 200,
            "data": [
                dict(UserProfileSerializer().to_representation(instance=self.user)),
                dict(UserProfileSerializer().to_representation(instance=self.user_2)),
            ],
        }
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)

    def test_search_with_matching_results(self):
        """Test search with matching result results."""
        query_params = {
            "search": "Pik",
        }
        url_with_params = f"{self.url}?{urlencode(query_params)}"
        expected_data = {
            "count": 1,
            "next": None,
            "previous": None,
            "status": "Success",
            "code": 200,
            "data": [
                dict(UserProfileSerializer().to_representation(instance=self.user_2))
            ],
        }

        response = self.client.get(url_with_params)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)

    def test_search_with_no_results(self):
        """Test search with no results."""
        query_params = {
            "search": "No Matching Result",
        }
        url_with_params = f"{self.url}?{urlencode(query_params)}"
        expected_data = {
            "count": 0,
            "next": None,
            "previous": None,
            "status": "Success",
            "code": 200,
            "data": [],
        }
        response = self.client.get(url_with_params)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)


class UserFollowerListAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.authenticated_user = UserModelFactory.create(is_active=True)

        self.follower_user_1 = UserModelFactory.create(
            email="follower1@example,com",
            is_active=True,
            first_name="Ragna",
            last_name="Rok",
        )
        self.follower_user_1_to_auth_record = FollowsFactory.create(
            user_to=self.authenticated_user, user_from=self.follower_user_1
        )

        self.follower_user_2 = UserModelFactory.create(
            email="follower2@example,com",
            is_active=True,
            first_name="Forde",
            last_name="Magna",
        )
        self.follower_user_2_to_auth_record = FollowsFactory.create(
            user_to=self.authenticated_user, user_from=self.follower_user_2
        )

        self.url = reverse("accounts_api_v1:user_follower_list")

    def test_list_fails_when_unauthenticated(self):
        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_list_authenticated_user_followers(self):
        self.client.force_authenticate(user=self.authenticated_user)
        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 2,
                "next": None,
                "previous": None,
                "status": "Success",
                "code": 200,
                "data": [
                    {
                        "created_datetime": serializers.DateTimeField().to_representation(
                            self.follower_user_2_to_auth_record.created_datetime
                        ),
                        "user": dict(
                            ProfileSerializer().to_representation(
                                instance=self.follower_user_2
                            )
                        ),
                    },
                    {
                        "created_datetime": serializers.DateTimeField().to_representation(
                            self.follower_user_1_to_auth_record.created_datetime
                        ),
                        "user": dict(
                            ProfileSerializer().to_representation(
                                instance=self.follower_user_1
                            )
                        ),
                    },
                ],
            },
        )

    def test_list_other_user_followers(self):
        self.client.force_authenticate(user=self.authenticated_user)
        # lets make authernticated_user follow follower_user_1
        auth_to_follower_user_1_record = FollowsFactory.create(
            user_from=self.authenticated_user, user_to=self.follower_user_1
        )

        url = f"{self.url}?{urlencode({'user_id': self.follower_user_1.id})}"
        response = self.client.get(path=url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "status": "Success",
                "code": 200,
                "data": [
                    {
                        "created_datetime": serializers.DateTimeField().to_representation(
                            auth_to_follower_user_1_record.created_datetime
                        ),
                        "user": dict(
                            ProfileSerializer().to_representation(
                                instance=self.authenticated_user
                            )
                        ),
                    }
                ],
            },
        )

        # list follower_2 followers (should be empty)
        url = f"{self.url}?{urlencode({'user_id': self.follower_user_2.id})}"
        response = self.client.get(path=url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 0,
                "next": None,
                "previous": None,
                "status": "Success",
                "code": 200,
                "data": [],
            },
        )


class UserFollowingListAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.authenticated_user = UserModelFactory.create(is_active=True)

        self.following_user_1 = UserModelFactory.create(
            email="follower1@example,com",
            is_active=True,
            first_name="Ragna",
            last_name="Rok",
        )

        self.follow_record_1 = FollowsFactory.create(
            user_from=self.authenticated_user,
            user_to=self.following_user_1,
        )

        self.user_2 = UserModelFactory.create(
            email="follower2@example,com",
            is_active=True,
            first_name="Forde",
            last_name="Magna",
        )

        UserGenericSettingsFactory.create(user=self.user_2)
        self.url = reverse("accounts_api_v1:user_following_list")

    def test_get_fails_when_unauthenticated(self):
        response = self.client.get(path=self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_get_authenticated_user_following_list(self):
        self.client.force_authenticate(self.authenticated_user)

        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "status": "Success",
                "code": 200,
                "data": [
                    {
                        "created_datetime": serializers.DateTimeField().to_representation(
                            self.follow_record_1.created_datetime
                        ),
                        "user": dict(
                            ProfileSerializer().to_representation(
                                instance=self.following_user_1
                            )
                        ),
                    },
                ],
            },
        )

    def test_get_other_user_following_list(self):
        self.client.force_authenticate(user=self.authenticated_user)

        # lets make user_2 follow user_1
        follow_record_2 = FollowsFactory.create(
            user_to=self.following_user_1,
            user_from=self.user_2,
        )

        url = f"{self.url}?{urlencode({'user_id': self.user_2.id})}"

        response = self.client.get(path=url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "status": "Success",
                "code": 200,
                "data": [
                    {
                        "created_datetime": serializers.DateTimeField().to_representation(
                            follow_record_2.created_datetime,
                        ),
                        "user": dict(
                            ProfileSerializer().to_representation(
                                instance=self.following_user_1
                            )
                        ),
                    },
                ],
            },
        )

        # lets get user_1's following list (should be empty)

        url = f"{self.url}?{urlencode({'user_id': self.following_user_1.id})}"
        response = self.client.get(path=url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "count": 0,
                "next": None,
                "previous": None,
                "status": "Success",
                "code": 200,
                "data": [],
            },
        )

    def test_post_fails_when_unauthenticated(self):
        response = self.client.post(path=self.url, data={"user_id": self.user_2.id})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_post_successfully(self):
        self.client.force_authenticate(self.authenticated_user)

        with patch(
            "uia_backend.notification.tasks.send_in_app_notification_task.delay"
        ) as mock_send_in_app_notification:
            response = self.client.post(self.url, data={"user_id": self.user_2.id})

        follow_records = Follows.objects.filter(
            user_from=self.authenticated_user, user_to=self.user_2
        )
        self.assertEqual(follow_records.count(), 1)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 201,
                "data": {
                    "created_datetime": serializers.DateTimeField().to_representation(
                        follow_records.first().created_datetime,
                    ),
                    "user": dict(
                        ProfileSerializer().to_representation(instance=self.user_2)
                    ),
                },
            },
        )

        mock_send_in_app_notification.assert_called_once_with(
            recipients=[self.user_2.id],
            verb="followed",
            actor_dict={
                "id": str(self.authenticated_user.id),
                "app_label": "accounts",
                "model_name": "customuser",
            },
            target_dict={
                "id": str(self.user_2.id),
                "app_label": "accounts",
                "model_name": "customuser",
            },
            notification_type=FOLLOW_USER_NOTIFICATION,
            data=dict(
                FollowingSerializer().to_representation(instance=follow_records.first())
            ),
        )

        # show that post is not affect by user_id query_param
        # but first lets delete the follow record
        follow_records.delete()

        with patch(
            "uia_backend.notification.tasks.send_in_app_notification_task.delay"
        ) as mock_send_in_app_notification:
            url = f"{self.url}?{urlencode({'user_id': self.user_2.id})}"
            response = self.client.post(url, data={"user_id": self.user_2.id})

        follow_records = Follows.objects.filter(
            user_from=self.authenticated_user, user_to=self.user_2
        )
        self.assertEqual(follow_records.count(), 1)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 201,
                "data": {
                    "created_datetime": serializers.DateTimeField().to_representation(
                        follow_records.first().created_datetime,
                    ),
                    "user": dict(
                        ProfileSerializer().to_representation(instance=self.user_2)
                    ),
                },
            },
        )

        mock_send_in_app_notification.assert_called_once_with(
            recipients=[self.user_2.id],
            verb="followed",
            actor_dict={
                "id": str(self.authenticated_user.id),
                "app_label": "accounts",
                "model_name": "customuser",
            },
            target_dict={
                "id": str(self.user_2.id),
                "app_label": "accounts",
                "model_name": "customuser",
            },
            notification_type=FOLLOW_USER_NOTIFICATION,
            data=dict(
                FollowingSerializer().to_representation(instance=follow_records.first())
            ),
        )

    def test_post_fails_if_user_is_already_being_followed(self):
        self.client.force_authenticate(self.authenticated_user)
        response = self.client.post(
            self.url, data={"user_id": self.following_user_1.id}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 400,
                "data": {"user_id": ["User already being followed."]},
            },
        )


class UserFollowingDetailAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.authenticated_user = UserModelFactory.create(is_active=True)

        self.following_user_1 = UserModelFactory.create(
            email="follower1@example,com",
            is_active=True,
            first_name="Ragna",
            last_name="Rok",
        )

        self.follow_record = FollowsFactory.create(
            user_from=self.authenticated_user,
            user_to=self.following_user_1,
        )

        self.user_2 = UserModelFactory.create(
            email="follower2@example,com",
            is_active=True,
            first_name="Forde",
            last_name="Magna",
        )

        UserGenericSettingsFactory.create(user=self.following_user_1)

    def test_delete_fails_when_unauthenticated(self):
        url = reverse(
            "accounts_api_v1:user_following_detail", args=[self.following_user_1.id]
        )

        response = self.client.delete(path=url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_delete_fails_if_user_is_not_being_followed(self):
        self.client.force_authenticate(self.authenticated_user)

        url = reverse("accounts_api_v1:user_following_detail", args=[self.user_2.id])
        response = self.client.delete(path=url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"status": "Error", "code": 404, "data": {"detail": "Not found."}},
        )

    def test_delete_successful(self):
        self.client.force_authenticate(self.authenticated_user)

        url = reverse(
            "accounts_api_v1:user_following_detail", args=[self.following_user_1.id]
        )

        with patch(
            "uia_backend.notification.tasks.send_in_app_notification_task.delay"
        ) as mock_send_in_app_notification:
            response = self.client.delete(path=url)

        data = {
            "recipients": [self.following_user_1.id],
            "verb": "un-followed",
            "actor_dict": {
                "id": str(self.authenticated_user.id),
                "app_label": "accounts",
                "model_name": "customuser",
            },
            "target_dict": {
                "id": str(self.following_user_1.id),
                "app_label": "accounts",
                "model_name": "customuser",
            },
            "notification_type": UNFOLLOW_USER_NOTIFICATION,
            "data": dict(
                FollowingSerializer().to_representation(instance=self.follow_record)
            ),
        }

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, None)

        self.assertFalse(
            Follows.objects.filter(
                user_from=self.authenticated_user, user_to=self.following_user_1
            ).exists()
        )

        mock_send_in_app_notification.assert_called_once_with(**data)


class UserGenericSettingsAPIViewTesTs(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        self.url = reverse("accounts_api_v1:user_settings")

    def test_get_fails_when_unauthenticated(self):
        response = self.client.get(path=self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_update_fails_when_unauthenticated(self):
        """Fails with 401 error because user is not authentiated."""

        data = {
            "notification": {
                "like": True,
                "comment": True,
                "follow": True,
                "share": True,
                "mention": True,
            }
        }

        response = self.client.patch(path=self.url, data=data)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_get_fails_when_user_settings_record_does_not_exits(self):
        """Fails and logs failure because settings record not found."""

        self.client.force_authenticate(self.user)

        with self.assertLogs() as log:
            response = self.client.get(path=self.url)

        print(log.records)
        self.assertEqual(len(log.records), 2)
        self.assertEqual(
            log.records[0].message,
            "uia_backend.accounts.api.v1.views.get_object:: User does not have UserGenericSettings record.",
        )
        self.assertEqual(log.records[0].user_id, self.user.id)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"status": "Error", "code": 404, "data": {"detail": "Not found."}},
        )

    def test_get_successful(self):
        generic_settings = UserGenericSettingsFactory.create(user=self.user)

        self.client.force_authenticate(self.user)

        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {"notification": generic_settings.notification},
            },
        )

    def test_update_successful(self):
        generic_settings = UserGenericSettingsFactory.create(user=self.user)

        self.client.force_authenticate(self.user)

        data = {
            "notification": {
                "like": False,
                "comment": True,
                "follow": False,
                "share": True,
                "mention": False,
            }
        }
        self.client.force_authenticate(self.user)
        response = self.client.patch(path=self.url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {"notification": data["notification"]},
            },
        )

        generic_settings.refresh_from_db()
        self.assertEqual(generic_settings.notification, data["notification"])
