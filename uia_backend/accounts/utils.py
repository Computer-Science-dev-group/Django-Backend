from dateutil.relativedelta import relativedelta
from django.core import signing
from django.urls import reverse
from django.utils import timezone
from rest_framework.request import Request

from uia_backend.accounts import constants
from uia_backend.accounts.models import EmailVerification
from uia_backend.notification.tasks import send_template_email_task


def send_user_registration_email_verification_mail(user, request: Request) -> None:
    """Send email to users to verifiy their email address."""

    verification_record = EmailVerification.objects.create(
        user=user,
        expiration_date=(
            timezone.now()
            + relativedelta(hours=constants.EMAIL_VERIFICATION_ACTIVE_PERIOD)
        ),
    )

    signer = signing.TimestampSigner()
    signature = signer.sign_object(str(verification_record.id))
    url = reverse("accounts_api_v1:email_verification", args=[signature])

    send_template_email_task.delay(
        recipients=[user.email],
        internal_tracker_ids=[str(verification_record.internal_tracker_id)],
        template_id=constants.EMAIL_VERIFICATION_TEMPLATE_ID,
        template_merge_data={
            user.email: {
                "link": request.build_absolute_uri(location=url),
                "expiration_duration_in_hours": constants.EMAIL_VERIFICATION_ACTIVE_PERIOD,
            },
        },
    )


def send_user_forget_password_mail(user, request: Request, otp) -> None:
    """Send email to users to reset their email address using OTP."""

    verification_record = EmailVerification.objects.create(
        user=user,
        expiration_date=(
            timezone.now()
            + relativedelta(hours=constants.EMAIL_VERIFICATION_ACTIVE_PERIOD)
        ),
    )

    send_template_email_task.delay(
        recipients=[user.email],
        internal_tracker_ids=[str(verification_record.internal_tracker_id)],
        template_id=constants.FORGET_PASSWORD_TEMPLATE_ID,
        template_merge_data={
            user.email: {
                "otp": otp,
                "expiration_duration_in_minutes": constants.OTP_ACTIVE_PERIOD,
            },
        },
    )
