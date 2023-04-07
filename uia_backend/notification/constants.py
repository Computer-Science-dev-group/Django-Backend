# EMAIL TRACKING
# https://anymail.dev/en/stable/sending/tracking/#event-tracking

# NOTE: we may want to add more event types but for now lets just track these
EMAIL_EVENT_TYPE_QUEUED = 1
EMAIL_EVENT_TYPE_REJECTED = 2
EMAIL_EVENT_TYPE_BOUNCED = 3
EMAIL_EVENT_TYPE_DEFFERED = 4
EMAIL_EVENT_TYPE_DELIVERED = 5
EMAIL_EVENT_TYPE_OPENED = 6

EMAIL_EVENT_TYPE_CHOICES = (
    (EMAIL_EVENT_TYPE_QUEUED, "queued"),
    (EMAIL_EVENT_TYPE_REJECTED, "rejected"),
    (EMAIL_EVENT_TYPE_BOUNCED, "bounced"),
    (EMAIL_EVENT_TYPE_DEFFERED, "deferred"),
    (EMAIL_EVENT_TYPE_DELIVERED, "delivered"),
    (EMAIL_EVENT_TYPE_OPENED, "opened"),
)
