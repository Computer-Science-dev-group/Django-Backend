import os

from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("uia_backend")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

CELERYBEAT_SCHEDULE = {
    # Deactivate expired email verification records runs every 6 hours
    # NOTE: subject to tuning
    "deactivate_expired_email_verification_records": {
        "task": "deactivate_expired_email_verification_records",
        "schedule": crontab(hour="*/6"),
    }
}
