from rest_framework.throttling import AnonRateThrottle


class PasswordRestThrottle(AnonRateThrottle):
    THROTTLE_RATES = {"anon": "1/minute"}
