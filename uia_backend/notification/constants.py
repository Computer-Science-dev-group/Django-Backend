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


# user follower notification events
FOLLOW_USER_NOTIFICATION = "new_follower_event"
UNFOLLOW_USER_NOTIFICATION = "unfollow_event"

# NOTIFICATION TYPES
NOTIFICATION_TYPE_CHOICES = (
    (FOLLOW_USER_NOTIFICATION, "New follower event"),
    (UNFOLLOW_USER_NOTIFICATION, "Unfollow event"),
)


# Cluster notification events
NOTIFICATION_TYPE_RECIEVED_CLUSTER_INVITATION = 1
NOTIFICATION_TYPE_CANCELED_CLUSTER_INVITATION = 2
NOTIFICATION_TYPE_ACCEPT_CLUSTER_INVITATION = 3
NOTIFICATION_TYPE_REJECT_CLUSTER_INVITATION = 4


NOTIFICATION_TYPE_CHOICES = (
    (NOTIFICATION_TYPE_RECIEVED_CLUSTER_INVITATION, "Recieved Cluster invitation"),
    (NOTIFICATION_TYPE_CANCELED_CLUSTER_INVITATION, "Cancelled Cluster Invitation"),
    (NOTIFICATION_TYPE_ACCEPT_CLUSTER_INVITATION, "Accepted Cluster Invitation"),
    (NOTIFICATION_TYPE_REJECT_CLUSTER_INVITATION, "Rejected Cluster Invitation"),
)
