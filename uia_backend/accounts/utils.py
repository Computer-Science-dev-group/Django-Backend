import logging

import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core import signing
from django.urls import reverse
from django.utils import timezone
from rest_framework.request import Request

from uia_backend.accounts import constants
from uia_backend.accounts.models import CustomUser, EmailVerification
from uia_backend.notification.tasks import send_template_email_task

Logger = logging.getLogger()


def send_user_registration_email_verification_mail(
    user: CustomUser, request: Request
) -> None:
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
            }
        },
    )


def get_location_from_ip(ip: str) -> str | None:
    """Get ip region from ipapi.co."""

    try:
        response = requests.get(url=f"{settings.IP_API_CO_URL}/{ip}/region/")
    except requests.HTTPError as error:
        Logger.error(
            "uia_backend::accounts::utils::get_location_from_ip:: HTTPError occured",
            extra={"detail": str(error)},
        )
        return
    # print(response.status_code)
    if response.status_code == 200:
        if response.text != "Undefined":
            return response.text
    elif response.status_code == 429:
        Logger.error(
            "uia_backend::accounts::utils::get_location_from_ip:: API free quota has been exceeded",
            extra={"detail": response.json()},
        )
    else:
        Logger.error(
            "uia_backend::accounts::utils::get_location_from_ip:: API error occured",
            extra={"detail": response.json()},
        )


def send_user_password_change_email_notification(
    user: CustomUser, request: Request
) -> None:
    """Send email to users to verify that their email has been reset."""

    ip_address = request.META["REMOTE_ADDR"]
    user_agent = request.META["HTTP_USER_AGENT"]
    region = get_location_from_ip(ip_address) or ""

    send_template_email_task.delay(
        recipients=[user.email],
        internal_tracker_ids=[str(user.id)],
        template_id=constants.PASSWORD_CHANGE_TEMPLATE_ID,
        template_merge_data={
            user.email: {
                "ip_address": ip_address,
                "user_agent": user_agent,
                "region": region,
            },
        },
    )
