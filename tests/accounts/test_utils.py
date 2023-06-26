from unittest import mock

import requests
import responses
from django.conf import settings
from django.core import signing
from django.http import HttpRequest
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.request import Request

from tests.accounts.test_models import UserModelFactory
from uia_backend.accounts import constants as account_constants
from uia_backend.accounts.models import EmailVerification
from uia_backend.accounts.utils import (
    generate_reset_password_otp,
    get_location_from_ip,
    send_user_password_change_email_notification,
    send_user_registration_email_verification_mail,
)


class SendUserRegistrationEmailVerificationMailTests(TestCase):
    def setUp(self):
        self.user = UserModelFactory.create()

    @override_settings(ALLOWED_HOSTS=["127.0.0.1"])
    def test_send_template_email(self):
        """Test mail was sent with correct details."""

        req = HttpRequest()
        req.META["HTTP_HOST"] = "127.0.0.1"
        req.META["SERVER_PORT"] = "8000"
        self.request = Request(request=req)

        with mock.patch(
            "uia_backend.notification.tasks.send_template_email_task.delay"
        ) as mock_send_email_task:
            send_user_registration_email_verification_mail(
                user=self.user, request=self.request
            )

        verification_record = EmailVerification.objects.filter(
            user=self.user,
            is_active=True,
        ).first()

        self.assertIsNotNone(verification_record)

        signer = signing.TimestampSigner()
        signature = signer.sign_object(str(verification_record.id))
        url = reverse("accounts_api_v1:email_verification", args=[signature])

        mock_send_email_task.assert_called_once_with(
            recipients=[self.user.email],
            internal_tracker_ids=[str(verification_record.internal_tracker_id)],
            template_id=account_constants.EMAIL_VERIFICATION_TEMPLATE_ID,
            template_merge_data={
                self.user.email: {
                    "link": self.request.build_absolute_uri(location=url),
                    "expiration_duration_in_hours": account_constants.EMAIL_VERIFICATION_ACTIVE_PERIOD,
                },
            },
        )


class GetLocationFromIpTests(TestCase):
    @responses.activate
    def test_happy_path_valid_ip(self):
        ip = "8.8.8.8"
        expected_region = "California"

        responses.add(
            responses.GET,
            f"{settings.IP_API_CO_URL}/{ip}/region/",
            body=expected_region,
            status=200,
        )
        result = get_location_from_ip(ip)
        self.assertEqual(result, expected_region)

    @responses.activate
    def test_edge_case_http_error(self):
        ip = "8.8.8.8"

        responses.add(
            responses.GET,
            f"{settings.IP_API_CO_URL}/{ip}/region/",
            body=requests.exceptions.HTTPError(),
        )

        with self.assertLogs(level="ERROR") as log:
            result = get_location_from_ip(ip)

        self.assertIsNone(result)
        self.assertEqual(
            log.output[0],
            "ERROR:root:"
            "uia_backend::accounts::utils::get_location_from_ip:: HTTPError occured",
        )

    @responses.activate
    def test_edge_case_invalid_ip(self):
        ip = "invalid_ip"
        responses.add(
            responses.GET,
            f"{settings.IP_API_CO_URL}/{ip}/region/",
            body="Undefined",
            status=200,
        )

        result = get_location_from_ip(ip)
        self.assertIsNone(result)

    @responses.activate
    def test_edge_case_api_error(self):
        ip = "8.8.8.8"
        responses.add(
            responses.GET,
            f"{settings.IP_API_CO_URL}/{ip}/region/",
            json={"error": "Internal Server Error"},
            status=500,
        )

        with self.assertLogs(level="ERROR") as log:
            result = get_location_from_ip(ip)

        self.assertIsNone(result)
        self.assertEqual(
            log.output[0],
            "ERROR:root:"
            "uia_backend::accounts::utils::get_location_from_ip:: API error occured",
        )

    @responses.activate
    def test_edge_case_api_quota_exceeded(self):
        ip = "127.0.0.1"
        responses.add(
            responses.GET,
            f"{settings.IP_API_CO_URL}/{ip}/region/",
            json={"error": "API quota exceeded"},
            status=429,
        )

        with self.assertLogs(level="ERROR") as log:
            result = get_location_from_ip(ip)

        self.assertIsNone(result)
        self.assertEqual(
            log.output[0],
            "ERROR:root:"
            "uia_backend::accounts::utils::get_location_from_ip:: API free quota has been exceeded",
        )


class SendUserPasswordChangeEmailNotificationTests(TestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        self.request = Request(HttpRequest())
        self.request.META["REMOTE_ADDR"] = "127.0.0.1"
        self.request.META["HTTP_USER_AGENT"] = "Mozilla/5.0"

    @responses.activate
    def test_send_user_password_change_email_notification(self):
        responses.add(
            responses.GET,
            f'{settings.IP_API_CO_URL}/{self.request.META["REMOTE_ADDR"]}/region/',
            body="Region",
            status=200,
        )

        with mock.patch(
            "uia_backend.notification.tasks.send_template_email_task.delay"
        ) as mock_send_email_task:
            send_user_password_change_email_notification(self.user, self.request)

        mock_send_email_task.assert_called_once
        mock_send_email_task.assert_called_once_with(
            recipients=[self.user.email],
            internal_tracker_ids=[str(self.user.id)],
            template_id=account_constants.PASSWORD_CHANGE_TEMPLATE_ID,
            template_merge_data={
                self.user.email: {
                    "ip_address": self.request.META["REMOTE_ADDR"],
                    "user_agent": self.request.META["HTTP_USER_AGENT"],
                    "region": "Region",
                },
            },
        )

    @responses.activate
    def test_send_user_password_change_email_notification_edge_case(self):
        responses.add(
            responses.GET,
            f'{settings.IP_API_CO_URL}/{self.request.META["REMOTE_ADDR"]}/region/',
            json={"error": "API quota exceeded"},
            status=429,
        )

        with mock.patch(
            "uia_backend.notification.tasks.send_template_email_task.delay"
        ) as mock_send_email_task:
            with self.assertLogs(level="ERROR") as log:
                send_user_password_change_email_notification(self.user, self.request)

        self.assertEqual(
            log.output[0],
            "ERROR:root:"
            "uia_backend::accounts::utils::get_location_from_ip:: API free quota has been exceeded",
        )
        mock_send_email_task.assert_called_once_with(
            recipients=[self.user.email],
            internal_tracker_ids=[str(self.user.id)],
            template_id=account_constants.PASSWORD_CHANGE_TEMPLATE_ID,
            template_merge_data={
                self.user.email: {
                    "ip_address": self.request.META["REMOTE_ADDR"],
                    "user_agent": self.request.META["HTTP_USER_AGENT"],
                    "region": "",
                },
            },
        )


class GenerateResetPasswordOtpTests(TestCase):
    @mock.patch(
        "uia_backend.accounts.utils.secrets.randbelow", side_effect=[1, 2, 3, 4, 5, 6]
    )
    def test_method(self, mock_secret):
        signer = signing.Signer()
        otp, signed_otp = generate_reset_password_otp()

        self.assertEqual(otp, "123456")
        self.assertEqual(signer.unsign(signed_otp), "123456")
