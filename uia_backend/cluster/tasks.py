from django.db.models import DateTimeField, ExpressionWrapper, F, Q
from django.utils import timezone

from config.celery_app import app as CELERY_APP
from uia_backend.cluster.models import ClusterInvitation


@CELERY_APP.task(name="deactivate_expired_cluster_invitation")
def deactivate_expired_cluster_invitation() -> None:
    """Deactivate user invitation records that have expired."""

    ClusterInvitation.objects.annotate(
        expected_expiration_datetime=ExpressionWrapper(
            F("created_datetime") + F("duration"),
            output_field=DateTimeField(),
        )
    ).filter(
        Q(status=ClusterInvitation.INVITATION_STATUS_PENDING)
        & Q(expected_expiration_datetime__lte=timezone.now())
    ).update(
        status=ClusterInvitation.INVITATION_STATUS_EXPIRED
    )
