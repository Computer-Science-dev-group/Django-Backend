import uuid

from dateutil.relativedelta import relativedelta
from django.core import signing
from django.utils import timezone

from tests.accounts.test_models import EmailVerificationFactory, UserModelFactory
from uia_backend.accounts.api.v1.serializers import (
    EmailVerificationSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)
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
        "email",
        "faculty",
        "department",
        "year_of_graduation",
    ]

    NON_REQUIRED_FIELDS = [
        "bio",
        "gender",
        "profile_picture",
        "cover_photo",
        "phone_number",
        "display_name",
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
            "lable": "Test valid data",
            "context": None,
        }
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
                "faculty": "Science",
                "department": "Computer Science",
                "year_of_graduation": str(
                    (timezone.now() + relativedelta(year=1)).year
                ),
            },
            "lable": "Test writing to year_of_graduation field failed",
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
