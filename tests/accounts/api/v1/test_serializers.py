import uuid

from dateutil.relativedelta import relativedelta
from django.core import signing
from django.utils import timezone

from tests.accounts.test_models import (
    EmailVerificationFactory,
    OTPFactory,
    UserModelFactory,
)
from uia_backend.accounts import constants
from uia_backend.accounts.api.v1.serializers import (
    ChangePasswordSerializer,
    EmailVerificationSerializer,
    ForgetPasswordSerializer,
    LoginSerializer,
    UserRegistrationSerializer,
    VerifyOTPSerializer,
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


class ForgetPasswordSerializerTestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(
            email="test@example.com",
            password="testpassword",
        )
        self.serializer = ForgetPasswordSerializer()
        self.serializer_class = ForgetPasswordSerializer

    def test_validate_email_with_valid_email(self):
        email = "test@example.com"
        result = self.serializer.validate_email(email)
        self.assertEqual(result, email)

    def test_validate_email_with_invalid_email(self):
        email = "invalidemail"
        with self.assertRaises(serializers.ValidationError):
            self.serializer.validate_email(email)

    def test_save(self):
        email = "test@example.com"
        serializer_data = {"email": email}
        self.serializer = self.serializer_class(
            data=serializer_data, context={"request": None}
        )
        self.serializer.is_valid()

        @patch("uia_backend.accounts.utils.send_user_forget_password_mail")
        def test_forget_password_serializer(self, mock_send_mail):
            self.serializer.save()
            otp = OTP.objects.get(user=self.user)
            self.assertEqual(otp.user, self.user)
            self.assertEqual(
                otp.expiry_time.minute,
                (timezone.now() + timezone.timedelta(minutes=30)).minute,
            )
            mock_send_mail.assert_called_once_with(self.user, None, otp=otp.otp)


class VerifyOTPSerializerTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.email = "test@example.com"
        cls.otp = "1234"
        cls.signer = signing.TimestampSigner()
        cls.signed_otp = cls.signer.sign(cls.otp)
        cls.new_password = "newpassword123"
        cls.user = CustomUser.objects.create(email=cls.email)
        cls.user.set_password(cls.new_password)
        cls.user.save()
        OTP.objects.create(
            user=cls.user,
            otp=cls.signed_otp,
            expiry_time=timezone.now() + timezone.timedelta(minutes=30),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        CustomUser.objects.filter(email=cls.email).delete()
        OTP.objects.filter(user=cls.user).delete()

    def test_validate_email(self):
        serializer = VerifyOTPSerializer(
            data={
                "email": self.email,
                "otp": self.otp,
                "new_password": self.new_password,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["email"], self.email)

    def test_validate_email_invalid(self):
        serializer = VerifyOTPSerializer(data={"email": "invalid@example.com"})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_validate(self):
        serializer = VerifyOTPSerializer(
            data={
                "email": self.email,
                "otp": self.otp,
                "new_password": self.new_password,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["email"], self.email)
        self.assertEqual(serializer.validated_data["otp"], self.otp)

    def test_validate_invalid_otp(self):
        serializer = VerifyOTPSerializer(data={"email": self.email, "otp": "6543"})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_validate_expired_otp(self):
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = OTP.objects.get(
                user=self.user
            ).expiry_time + timezone.timedelta(seconds=1)
            serializer = VerifyOTPSerializer(
                data={"email": self.email, "otp": self.otp}
            )
            with self.assertRaises(ValidationError):
                serializer.is_valid(raise_exception=True)

    def test_save(self):
        serializer = VerifyOTPSerializer(
            data={
                "email": self.email,
                "otp": self.otp,
                "new_password": self.new_password,
            }
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))
        self.assertFalse(OTP.objects.get(otp=self.signed_otp).is_active)
        # self.assertIsNotNone(Token.objects.get(user=self.user))
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


class ForgetPasswordSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = ForgetPasswordSerializer

    REQUIRED_FIELDS = ["email"]
    NON_REQUIRED_FIELDS = []

    def setUp(self) -> None:
        user = UserModelFactory.create(email="user@example.com")
        user.set_password("thestrongestpassword")
        user.save()

        self.VALID_DATA = [
            {
                "data": {
                    "email": "user@example.com",
                },
                "lable": "Test valid data",
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "email": "noob@invalid.com",
                },
                "lable": "Test invalid bad email",
            },
            {
                "data": {
                    "email": "nonexistent.com",
                },
                "lable": "Invalid Email Record",
            },
        ]


class VerifyOTPSerializerTests(CustomSerializerTests):
    __test__ = True

    serializer_class = VerifyOTPSerializer

    REQUIRED_FIELDS = ["email", "otp", "new_password"]
    NON_REQUIRED_FIELDS = []

    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com")
        self.user.set_password("thestrongestpassword")
        self.user.save()

        self.otp_val = "1234"
        self.signer = signing.TimestampSigner()
        self.signed_otp = self.signer.sign(self.otp_val)

        self.new_password = "newpassword1"

        self.otp = OTPFactory.create(
            user=self.user,
            otp=self.signed_otp,
            expiry_time=timezone.now()
            + timezone.timedelta(minutes=constants.OTP_MINUTES_EXPIRY_TIME),
        )

        self.invalid_otp = OTPFactory.create(
            user=self.user,
            otp=self.signed_otp,
            expiry_time=timezone.now() - timezone.timedelta(minutes=31),
        )

        self.VALID_DATA = [
            {
                "data": {
                    "email": self.user.email,
                    "otp": self.otp_val,
                    "new_password": self.new_password,
                },
                "lable": "Test valid data",
            }
        ]

        self.INVALID_DATA = [
            {
                "data": {
                    "email": "noob@invalid.com",
                    "otp": self.otp,
                    "new_password": self.new_password,
                },
                "lable": "Test invalid bad email",
            },
            {
                "data": {
                    "email": self.user.email,
                    "otp": "wontwork",
                    "new_password": self.new_password,
                },
                "lable": "Test Invalid OTP",
            },
        ]
