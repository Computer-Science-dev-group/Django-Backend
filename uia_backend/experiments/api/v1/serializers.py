from logging import getLogger
from typing import Any

from django.db.models import F
from rest_framework import serializers

from uia_backend.experiments.constants import ER_001_PRE_ALPHA_USER_TESTING_TAG
from uia_backend.experiments.models import PreAlphaUserTestingExperiment

logger = getLogger()


class PreAplhaTestingPopulationSerializer(serializers.Serializer):
    enrolled_user_population = serializers.IntegerField(default=0, read_only=True)
    max_allowed_user_population = serializers.IntegerField(default=0, read_only=True)

    def create(self, validated_data: Any) -> Any:
        """Overridden method"""

    def update(self, instance: Any, validated_data: Any) -> Any:
        """Overidden method"""

    def to_representation(self, instance: Any) -> Any:
        exprriment_population = PreAlphaUserTestingExperiment.objects.filter(
            experiment_config__experiment_tag=ER_001_PRE_ALPHA_USER_TESTING_TAG,
            experiment_config__is_active=True,
        ).annotate(
            max_allowed_user_population=F(
                "experiment_config__required_user_population"
            ),
        )

        return {
            "enrolled_user_population": exprriment_population.count(),
            "max_allowed_user_population": exprriment_population[
                0
            ].max_allowed_user_population
            if exprriment_population
            else 0,
        }
