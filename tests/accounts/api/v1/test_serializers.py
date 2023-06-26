import random
import uuid

from dateutil.relativedelta import relativedelta
from django.core import signing
from django.utils import timezone

from tests.accounts.test_models import (
    EmailVerificationFactory,
    PasswordResetAttemptFactory,
    UserModelFactory,
)
from uia_backend.accounts.api.v1.serializers import (
    ChangePasswordSerializer,
    EmailVerificationSerializer,
    FollowsSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    RestPasswordRequestSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    VerifyResetPasswordOTPSerializer,
)
from uia_backend.accounts.models import PasswordResetAttempt
from uia_backend.libs.testutils import CustomSerializerTests


class UserRegistrationSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = UserRegistrationSerializer

    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "email",
        "password",
        "faculty",
        "department",
        "year_of_graduation",
    ]

    NON_REQUIRED_FIELDS = []

    VALID_DATA = [
        {
            "data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "user@example.com",
                "password": "f_g68Ata7jPqqmm",
                "faculty": "Science",
                "department": "Computer Science",
                "year_of_graduation": "2001",
            },
            "lable": "Test valid data",
            "context": None,
        }
    ]

    INVALID_DATA = [
        {
            "data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "user@example.com",
                "password": "f_g68Ata7jPqqmm",
                "faculty": "Science",
                "department": "Computer Science",
                "year_of_graduation": "1901",
            },
            "lable": "Test invalid year_of_graduation 1",
            "context": None,
        },
        {
            "data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "user@example.com",
                "password": "f_g68Ata7jPqqmm",
                "faculty": "Science",
                "department": "Computer Science",
                "year_of_graduation": str(
                    (timezone.now() + relativedelta(year=1)).year
                ),
            },
            "lable": "Test invalid year_of_graduation 2",
            "context": None,
        },
        {
            "data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "user@example.com",
                "password": "f_g68Ata7jPqqmm",
                "faculty": "Science",
                "department": "Computer Science",
                "year_of_graduation": "2s21",
            },
            "lable": "Test invalid year_of_graduation format 3",
            "context": None,
        },
        {
            "data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "user@example.com",
                "password": "string",
                "faculty": "Science",
                "department": "Computer Science",
                "year_of_graduation": "2001",
            },
            "lable": "Test invalid password",
            "context": None,
        },
    ]


class EmailVerificationSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = EmailVerificationSerializer

    REQUIRED_FIELDS = ["signature"]
    NON_REQUIRED_FIELDS = []

    def setUp(self) -> None:
        user = UserModelFactory.create()
        verification_record = EmailVerificationFactory.create(
            expiration_date=(timezone.now() + relativedelta(days=34)), user=user
        )

        signer = signing.TimestampSigner()
        signature = signer.sign_object(str(verification_record.id))

        self.VALID_DATA = [
            {
                "data": {
                    "signature": signature,
                },
                "lable": "Test valid data",
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "signature": "asjnj-lsndjka-nsdnxswsn.dnas-mdnamsnd",
                },
                "lable": "Test invalid bad signature",
            },
            {
                "data": {
                    "signature": signer.sign_object(str(uuid.uuid4())),
                },
                "lable": "Invalid Email Record",
            },
        ]


class UserProfileSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = UserProfileSerializer

    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "display_name",
    ]

    NON_REQUIRED_FIELDS = [
        "profile_picture",
        "cover_photo",
        "phone_number",
        "bio",
        "gender",
        "date_of_birth",
        "year_of_graduation",
        "department",
        "faculty",
    ]

    VALID_DATA = [
        {
            "data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "user@example.com",
                "password": "f_g68Ata7jPqqmm",
                "faculty": "Science",
                "department": "Computer Science",
                "year_of_graduation": "2001",
                "bio": "Hi, I am a graduate of Computer Science, UI",
                "gender": "Male",
                "display_name": "John Peters",
                "phone_number": "08020444345",
            },
        },
    ]

    INVALID_DATA = [
        {
            "data": {
                "first_name": "",
                "last_name": "",
                "email": "user@example.com",
                "faculty": "Science",
                "department": "Computer Science",
                "year_of_graduation": "1901",
            },
            "lable": "Test first_name and last_name failed",
            "context": None,
        },
        {
            "data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "user@example.com",
                "password": "f_g68Ata7jPqqmm",
                "faculty": "Science",
                "department": "",
                "year_of_graduation": "2s21",
            },
            "lable": "Test writing to department field failed",
            "context": None,
        },
        {
            "data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "user@example.com",
                "faculty": "",
                "department": "Computer Science",
                "year_of_graduation": "2001",
            },
            "lable": "Test writing to faculty field failed",
            "context": None,
        },
    ]


class ChangePasswordSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = ChangePasswordSerializer

    REQUIRED_FIELDS = ["password"]
    NON_REQUIRED_FIELDS = []

    VALID_DATA = [
        {
            "data": {"password": "f_g68Ata7jPqqmm"},
            "lable": "Test valid data",
            "context": None,
        }
    ]

    INVALID_DATA = [
        {
            "data": {"password": "string"},
            "lable": "Test invalid password lenght",
            "context": None,
        }
    ]

class FollowsSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = FollowsSerializer

    REQUIRED_FIELDS = ["user_from", "user_to"]
    NON_REQUIRED_FIELDS = []

    def setUp(self) -> None:
        user_1 = UserModelFactory.create(email="user1@example.com", is_active=True, is_verified=True)
        user_1.set_password("12345")
        user_1.save()

        user_2 = UserModelFactory.create(email="user2@example.com", is_active=True, is_verified=True)
        user_2.set_password("12345")
        user_2.save()

        self.VALID_DATA = [
            {
                "data": { "user_from": self.user_1, "user_to": self.user_2 },
                "lable": "Test valid data",
                "context": None,
            }
        ]

        self.INVALID_DATA = [
            {
                "data": { "user_from": "string", "user_to": "string" }
                "lable": "Test invalid data for follow relationship between users",
                "context": None,
            }
        ]

class LoginSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = LoginSerializer

    REQUIRED_FIELDS = ["email", "password"]
    NON_REQUIRED_FIELDS = []

    def setUp(self) -> None:
        user = UserModelFactory.create(email="user@example.com", is_active=True)

        user.set_password("12345")
        user.save()

        inactive_user = UserModelFactory.create(
            email="inactive@example.com",
            is_active=False,
        )

        inactive_user.set_password("12345")
        inactive_user.save()

        self.VALID_DATA = [
            {
                "data": {"password": "12345", "email": "user@example.com"},
                "lable": "Test valid data",
                "context": None,
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {"password": "12345", "email": "wrong@example.com"},
                "lable": "Test invalid data wrong email.",
                "context": None,
            },
            {
                "data": {"password": "xxxxxx", "email": "user@example.com"},
                "lable": "Test invalid data wrong password.",
                "context": None,
            },
            {
                "data": {"password": "12345", "email": "wrong@example.com"},
                "lable": "Test invalid data wrong email.",
                "context": None,
            },
            {
                "data": {"password": "12345", "email": "inactive@example.com"},
                "lable": "Test invalid inactive user.",
                "context": None,
            },
        ]


class RestPasswordRequestSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = RestPasswordRequestSerializer

    REQUIRED_FIELDS = ["email"]
    NON_REQUIRED_FIELDS = []

    def setUp(self) -> None:
        active_user = UserModelFactory.create(email="user@example.com", is_active=True)
        inactive_user = UserModelFactory.create(
            email="inactive@example.com", is_active=False
        )

        self.VALID_DATA = [
            {
                "data": {
                    "email": active_user.email,
                },
                "lable": "Test valid data",
                "context": None,
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "email": "",
                },
                "lable": "Test empty email",
                "context": None,
            },
            {
                "data": {
                    "email": "invalid_email_address",
                },
                "lable": "Test invalid email address",
                "context": None,
            },
            {
                "data": {
                    "email": inactive_user.email,
                },
                "lable": "Test inactive email address",
                "context": None,
            },
            {
                "data": {
                    "email": "some_non_existent_user@example.com",
                },
                "lable": "Test non-existent email address",
                "context": None,
            },
        ]


class VerifyResetPasswordOTPSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = VerifyResetPasswordOTPSerializer

    REQUIRED_FIELDS = ["otp", "email"]
    NON_REQUIRED_FIELDS = ["password_change_key"]

    def setUp(self) -> None:
        user = UserModelFactory.create(is_active=True)

        otp = 333555
        signer = signing.Signer()
        pending_signature = signer.sign(str(otp))

        PasswordResetAttemptFactory.create(
            expiration_datetime=(timezone.now() + relativedelta(minutes=10)),
            signed_otp=pending_signature,
            user=user,
            status=PasswordResetAttempt.STATUS_PENDING,
        )

        PasswordResetAttemptFactory.create(
            user=user,
            expiration_datetime=(timezone.now() + relativedelta(minutes=10)),
            signed_otp=signer.sign("111111"),
            status=random.choice(
                [
                    PasswordResetAttempt.STATUS_EXPIRED,
                    PasswordResetAttempt.STATUS_OTP_VERIFIED,
                    PasswordResetAttempt.STATUS_SUCCESS,
                ]
            ),
        )

        self.VALID_DATA = [
            {
                "data": {
                    "otp": str(otp),
                    "email": user.email,
                },
                "lable": "Test valid data",
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "otp": "000000",
                    "email": user.email,
                },
                "lable": "Test invalid otp signature",
            },
            {
                "data": {
                    "otp": "111111",
                    "email": user.email,
                },
                "lable": "Non pending otp",
            },
            {
                "data": {
                    "otp": str(otp),
                    "email": "invalid_email@example.com",
                },
                "lable": "Test invalid email",
            },
        ]


class ResetPasswordSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = ResetPasswordSerializer

    REQUIRED_FIELDS = ["new_password", "email", "password_change_key"]
    NON_REQUIRED_FIELDS = []

    def setUp(self) -> None:
        user = UserModelFactory.create(is_active=True)

        otp = 333555
        signer = signing.Signer()
        pending_signature = signer.sign(str(otp))

        verified_password_reset_record = PasswordResetAttemptFactory.create(
            expiration_datetime=(timezone.now() + relativedelta(minutes=10)),
            signed_otp=pending_signature,
            user=user,
            status=PasswordResetAttempt.STATUS_OTP_VERIFIED,
        )

        non_verified_password_reset_record = PasswordResetAttemptFactory.create(
            user=user,
            expiration_datetime=(timezone.now() + relativedelta(minutes=10)),
            signed_otp=signer.sign("111111"),
            status=random.choice(
                [
                    PasswordResetAttempt.STATUS_EXPIRED,
                    PasswordResetAttempt.STATUS_PENDING,
                    PasswordResetAttempt.STATUS_SUCCESS,
                ]
            ),
        )

        self.VALID_DATA = [
            {
                "data": {
                    "new_password": "f_g68Ata7jPqqmm",
                    "email": user.email,
                    "password_change_key": verified_password_reset_record.generate_signed_identifier(),
                },
                "lable": "Test valid data",
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "new_password": "f_g68Ata7jPqqmm",
                    "email": user.email,
                    "password_change_key": non_verified_password_reset_record.generate_signed_identifier(),
                },
                "lable": "Non verified otp signature",
            },
            {
                "data": {
                    "new_password": "f_g68Ata7jPqqmm",
                    "email": "invalid_email@example.com",
                    "password_change_key": verified_password_reset_record.generate_signed_identifier(),
                },
                "lable": "Invalid email address.",
            },
            {
                "data": {
                    "new_password": "string",
                    "email": user.email,
                    "password_change_key": verified_password_reset_record.generate_signed_identifier(),
                },
                "lable": "Invalid password.",
            },
        ]
