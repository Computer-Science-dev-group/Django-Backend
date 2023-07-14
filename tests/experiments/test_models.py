from factory.django import DjangoModelFactory

from uia_backend.experiments.constants import EXPERIMENT_SELECTION_TYPE_FFS
from uia_backend.experiments.models import (
    ExperimentConfig,
    PreAlphaUserTestingExperiment,
)


class ExperimentConfigFactory(DjangoModelFactory):
    required_user_population = 100
    selection_type = EXPERIMENT_SELECTION_TYPE_FFS
    is_active = True

    class Meta:
        model = ExperimentConfig


class PreAlphaUserTestingExperimentFactory(DjangoModelFactory):
    class Meta:
        model = PreAlphaUserTestingExperiment
