from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class PasswordRestThrottle(AnonRateThrottle):
    THROTTLE_RATES = {"anon": "1/minute"}


class ChangePassswordThrottle(UserRateThrottle):
    scope = "sustained"
    rate = "1/minute"
