from logging import getLogger

from uia_backend.accounts.models import CustomUser
from uia_backend.experiments.constants import (
    ER_001_CONFIG,
    ER_001_PRE_ALPHA_USER_TESTING_TAG,
)
from uia_backend.experiments.models import (
    ExperimentConfig,
    PreAlphaUserTestingExperiment,
)

logger = getLogger()


def enroll_user_to_prealpha_testing_experiment(user: CustomUser):
    """Enroll a user to the preapha tesing experiment."""

    # first we retrieve the experiment config record
    experiment_model, _ = ExperimentConfig.objects.get_or_create(
        experiment_tag=ER_001_PRE_ALPHA_USER_TESTING_TAG,
        defaults=ER_001_CONFIG,
    )

    # next we check that expriment is active
    if not experiment_model.is_active:
        logger.warning(
            "uia_backend::experiments::utils::enroll_user_to_prealpha_testing_experiment:: Experiment is not active.",
            extra={
                "experiment_config_id": str(experiment_model.id),
                "experiment_tag": experiment_model.experiment_tag,
            },
        )

        return

    # next we check if experiment has reached its capacity
    enrolled_user_count = PreAlphaUserTestingExperiment.objects.filter(
        experiment_config__experiment_tag=ER_001_PRE_ALPHA_USER_TESTING_TAG,
    ).count()
    if experiment_model.required_user_population <= enrolled_user_count:
        logger.warning(
            "uia_backend::experiments::utils::enroll_user_to_prealpha_testing_experiment:: "
            "Experiment has reached capacity.",
            extra={
                "experiment_config_id": str(experiment_model.id),
                "experiment_tag": experiment_model.experiment_tag,
                "capacity": experiment_model.required_user_population,
            },
        )
        return

    # enroll the user into the expriement
    PreAlphaUserTestingExperiment.objects.get_or_create(
        user=user, defaults={"experiment_config": experiment_model}
    )
