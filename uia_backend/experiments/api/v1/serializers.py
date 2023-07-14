from logging import getLogger
from typing import Any

from rest_framework import serializers

from uia_backend.experiments.constants import ER_001_PRE_ALPHA_USER_TESTING_TAG
from uia_backend.experiments.models import (
    ExperimentConfig,
    PreAlphaUserTestingExperiment,
)

logger = getLogger()


class PreAplhaTestingPopulationSerializer(serializers.Serializer):
    enrolled_user_population = serializers.IntegerField(default=0, read_only=True)
    max_allowed_user_population = serializers.IntegerField(default=0, read_only=True)

    def create(self, validated_data: Any) -> Any:
        """Overridden method"""

    def update(self, instance: Any, validated_data: Any) -> Any:
        """Overidden method"""

    def to_representation(self, instance: Any) -> Any:
        try:
            er_config = ExperimentConfig.objects.get(
                experiment_tag=ER_001_PRE_ALPHA_USER_TESTING_TAG, is_active=True
            )
        except ExperimentConfig.DoesNotExist:
            logger.error(
                "uia_backend::accounts::api::v1::views::UserRegistrationAPIView::"
                " ExperimentConfig not found | is inactive.",
                exc_info={"experiment_tag": ER_001_PRE_ALPHA_USER_TESTING_TAG},
            )
            return {"enrolled_user_population": 0, "max_allowed_user_population": 0}

        return {
            "enrolled_user_population": PreAlphaUserTestingExperiment.objects.filter(
                experiment_config=er_config
            ).count(),
            "max_allowed_user_population": er_config.required_user_population,
        }
