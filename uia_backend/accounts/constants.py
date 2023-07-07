MIN_ALLOWED_GRADUATION_YEAR = "1948"

# how long an email verification mail should last in hours before expiration
EMAIL_VERIFICATION_ACTIVE_PERIOD = 24

# how long a password reset otp should last in minutes before expiration
PASSWORD_RESET_ACTIVE_PERIOD = 10
PASSWORD_RESET_OTP_LENGTH = 6

# NOTE :Joseph you need to find a better way to sort email templates for cases where we need to switch ESPs
EMAIL_VERIFICATION_TEMPLATE_ID = "d-1dda679ebf2846b498b6ab027a4f73b7"
PASSWORD_CHANGE_TEMPLATE_ID = "d-7cdf816164d64d0791b9b0b6f9a7ffff"
PASSWORD_RESET_TEMPLATE_ID = "d-3a50ac41a1654b548f8521e1ae40bad4"

# This is for creating or updating user handle
HANDLE_CREATION = "handle-creation"
HANDLE_UPDATE = "handle-update"
CACHE_DURATION = 3600
