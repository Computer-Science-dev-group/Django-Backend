from unittest import mock

from django.core import signing
from django.http import HttpRequest
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.request import Request

from tests.accounts.test_models import UserModelFactory
from uia_backend.accounts import constants as account_constants
from uia_backend.accounts.models import EmailVerification
from uia_backend.accounts.utils import send_user_registration_email_verification_mail


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
