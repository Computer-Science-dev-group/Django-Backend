from django.db import models

from uia_backend.accounts.models import CustomUser
from uia_backend.experiments.constants import EXPERIMENT_SELECTION_TYPE_CHOICES
from uia_backend.libs.base_models import BaseAbstractModel


class ExperimentConfig(BaseAbstractModel):
    experiment_tag = models.CharField(max_length=100, db_index=True, unique=True)
    required_user_population = models.IntegerField(default=0)
    selection_type = models.IntegerField(choices=EXPERIMENT_SELECTION_TYPE_CHOICES)
    experiment_duration = models.DurationField(null=True)
    meta_data = models.JSONField(default={})
    is_active = models.BooleanField(default=True)


class PreAlphaUserTestingExperiment(BaseAbstractModel):
    """Model representing users onboarded on the Pre-aplha testing experiment"""

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    experiment_config = models.ForeignKey(ExperimentConfig, on_delete=models.PROTECT)
