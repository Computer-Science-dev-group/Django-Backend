import random
import uuid
from unittest.mock import MagicMock

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
    FollowerSerializer,
    FollowingSerializer,
    FriendshipInvitationSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    RestPasswordRequestSerializer,
    UserFriendShipSettingsSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    VerifyResetPasswordOTPSerializer,
)
from uia_backend.accounts.models import PasswordResetAttempt
from uia_backend.libs.testutils import CustomSerializerTests, get_test_image_file


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
            "label": "Test valid data",
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
            "label": "Test invalid year_of_graduation 1",
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
            "label": "Test invalid year_of_graduation 2",
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
            "label": "Test invalid year_of_graduation format 3",
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
            "label": "Test invalid password",
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
                "label": "Test valid data",
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "signature": "asjnj-lsndjka-nsdnxswsn.dnas-mdnamsnd",
                },
                "label": "Test invalid bad signature",
            },
            {
                "data": {
                    "signature": signer.sign_object(str(uuid.uuid4())),
                },
                "label": "Invalid Email Record",
            },
        ]


class UserProfileSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = UserProfileSerializer

    REQUIRED_FIELDS = ["first_name", "last_name", "display_name", "gender"]

    NON_REQUIRED_FIELDS = [
        "id",
        "profile_picture",
        "cover_photo",
        "phone_number",
        "bio",
        "date_of_birth",
        "year_of_graduation",
        "department",
        "faculty",
        "follower_count",
        "following_count",
        "ws_channel_name",
    ]

    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        request = MagicMock()
        request.user = self.user

        self.VALID_DATA = [
            {
                "data": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "bio": "Hi, I am a graduate of Computer Science, UI",
                    "gender": "Male",
                    "display_name": "John-Peters",
                    "phone_number": "08020444345",
                    "cover_photo": get_test_image_file(),
                    "profile_picture": get_test_image_file(),
                },
                "label": "Test valid data with all write fields",
                "context": {"request": request},
            },
            {
                "data": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "bio": "Hi, I am a graduate of Computer Science, UI",
                    "gender": "Female",
                    "display_name": "John_Peters",
                    "phone_number": "08020444345",
                    "cover_photo": get_test_image_file(),
                    "profile_picture": get_test_image_file(),
                },
                "label": "Test valid data with all write fields",
                "context": {"request": request},
            },
            {
                "data": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "display_name": "_John-Peters_",
                    "gender": "Male",
                },
                "label": "Test valid data with required fields.",
                "context": {"request": request},
            },
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "first_name": "",
                    "last_name": "Assas",
                    "display_name": "Johnsnow",
                    "gender": "Male",
                },
                "label": "Test first_name is required",
                "context": {"request": request},
            },
            {
                "data": {
                    "first_name": "John",
                    "last_name": "",
                    "display_name": "Johnsnow",
                    "gender": "Male",
                },
                "label": "Test last_name is required",
                "context": {"request": request},
            },
            {
                "data": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "display_name": "",
                    "gender": "Male",
                },
                "label": "Test display_name is required",
                "context": {"request": request},
            },
            {
                "data": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "display_name": "Johnsnow",
                    "gender": "",
                },
                "label": "Test gener is required",
                "context": {"request": request},
            },
            {
                "data": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "display_name": "Johnsnow",
                    "gender": "Stray",
                },
                "label": "Test invalid gender option",
                "context": {"request": request},
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
            "label": "Test valid data",
            "context": None,
        }
    ]

    INVALID_DATA = [
        {
            "data": {"password": "string"},
            "label": "Test invalid password lenght",
            "context": None,
        }
    ]


class LoginSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = LoginSerializer

    REQUIRED_FIELDS = ["email", "password"]
    NON_REQUIRED_FIELDS = ["auth_token", "refresh_token", "profile", "ws_token"]

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
                "label": "Test valid data",
                "context": None,
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {"password": "12345", "email": "wrong@example.com"},
                "label": "Test invalid data wrong email.",
                "context": None,
            },
            {
                "data": {"password": "xxxxxx", "email": "user@example.com"},
                "label": "Test invalid data wrong password.",
                "context": None,
            },
            {
                "data": {"password": "12345", "email": "wrong@example.com"},
                "label": "Test invalid data wrong email.",
                "context": None,
            },
            {
                "data": {"password": "12345", "email": "inactive@example.com"},
                "label": "Test invalid inactive user.",
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
                "label": "Test valid data",
                "context": None,
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "email": "",
                },
                "label": "Test empty email",
                "context": None,
            },
            {
                "data": {
                    "email": "invalid_email_address",
                },
                "label": "Test invalid email address",
                "context": None,
            },
            {
                "data": {
                    "email": inactive_user.email,
                },
                "label": "Test inactive email address",
                "context": None,
            },
            {
                "data": {
                    "email": "some_non_existent_user@example.com",
                },
                "label": "Test non-existent email address",
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
                "label": "Test valid data",
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "otp": "000000",
                    "email": user.email,
                },
                "label": "Test invalid otp signature",
            },
            {
                "data": {
                    "otp": "111111",
                    "email": user.email,
                },
                "label": "Non pending otp",
            },
            {
                "data": {
                    "otp": str(otp),
                    "email": "invalid_email@example.com",
                },
                "label": "Test invalid email",
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
                "label": "Test valid data",
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "new_password": "f_g68Ata7jPqqmm",
                    "email": user.email,
                    "password_change_key": non_verified_password_reset_record.generate_signed_identifier(),
                },
                "label": "Non verified otp signature",
            },
            {
                "data": {
                    "new_password": "f_g68Ata7jPqqmm",
                    "email": "invalid_email@example.com",
                    "password_change_key": verified_password_reset_record.generate_signed_identifier(),
                },
                "label": "Invalid email address.",
            },
            {
                "data": {
                    "new_password": "string",
                    "email": user.email,
                    "password_change_key": verified_password_reset_record.generate_signed_identifier(),
                },
                "label": "Invalid password.",
            },
        ]


class FriendshipInvitationSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = FriendshipInvitationSerializer

    REQUIRED_FIELDS = ["sent_to"]
    NON_REQUIRED_FIELDS = [
        "id",
        "status",
        "created_by",
        "created_datetime",
        "updated_datetime",
    ]

    def setUp(self) -> None:
        authenticated_user = UserModelFactory.create(
            email="email1@example.com",
        )
        invited_user = UserModelFactory.create(
            email="email2@example.com",
        )

        inactive_user = UserModelFactory.create(
            is_active=False, email="email3@example.com"
        )

        request = MagicMock()
        request.user = authenticated_user

        # Test data for sending invitation
        self.VALID_DATA = [
            {
                "data": {
                    "status": 0,
                    "sent_to": str(invited_user.id),
                },
                "label": "Test valid data",
                "context": {"request": request},
            },
            {
                "data": {"sent_to": str(invited_user.id)},
                "label": "Test valid data",
                "context": {"request": request},
            },
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "status": 5,
                    "sent_to": str(invited_user.id),
                },
                "label": "Test invalid status",
                "context": {"request": request},
            },
            {
                "data": {
                    "status": 0,
                    "sent_to": str(uuid.uuid4()),
                },
                "label": "Test invalid user",
                "context": {"request": request},
            },
            {
                "data": {
                    "status": 0,
                    "sent_to": str(authenticated_user.id),
                },
                "label": "Test invalid user. Can not send invitation to yourself.",
                "context": {"request": request},
            },
            {
                "data": {
                    "status": 0,
                    "sent_to": str(inactive_user.id),
                },
                "label": "Test invalid user. Can invite inactive user.",
                "context": {"request": request},
            },
        ]


class UserFriendShipSettingsSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = UserFriendShipSettingsSerializer

    REQUIRED_FIELDS = []

    NON_REQUIRED_FIELDS = [
        "id",
        "users",
        "is_blocked",
        "created_datetime",
        "updated_datetime",
        "friendship_id",
    ]

    VALID_DATA = [
        {
            "data": {
                "is_blocked": True,
            },
            "label": "Test valid data",
        },
        {
            "data": {
                "is_blocked": False,
            },
            "label": "Test valid data",
        },
    ]

    INVALID_DATA = []


class FollowingSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = FollowingSerializer

    REQUIRED_FIELDS = ["user_id"]
    NON_REQUIRED_FIELDS = ["user", "created_datetime"]

    def setUp(self) -> None:
        user = UserModelFactory.create(email="user@example.com")
        request = MagicMock()
        request.user = user

        self.VALID_DATA = [
            {
                "data": {"user_id": user.id},
                "label": "Test valid data.",
                "context": {"request": request},
            }
        ]

        self.INVALID_DATA = [
            {"data": {"user_id": uuid.uuid4()}, "label": "Test invalid user_id data."}
        ]


class FollowerSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = FollowerSerializer

    REQUIRED_FIELDS = []
    NON_REQUIRED_FIELDS = ["user", "created_datetime"]

    VALID_DATA = []
    INVALID_DATA = []
