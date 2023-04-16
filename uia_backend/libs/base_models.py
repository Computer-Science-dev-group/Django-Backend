import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseAbstractModel(models.Model):
    """Base model"""

    id = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, editable=False, primary_key=True
    )
    created_datetime = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_datetime = models.DateTimeField(_("Last update at"), auto_now=True)

    objects = models.Manager()

    class Meta:
        abstract = True

