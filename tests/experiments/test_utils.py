from django.test import TestCase

from tests.accounts.test_models import UserModelFactory
from tests.experiments.test_models import ExperimentConfigFactory
from uia_backend.experiments.constants import (
    ER_001_PRE_ALPHA_USER_TESTING_TAG,
    EXPERIMENT_SELECTION_TYPE_FFS,
)
from uia_backend.experiments.models import (
    ExperimentConfig,
    PreAlphaUserTestingExperiment,
)
from uia_backend.experiments.utils import enroll_user_to_prealpha_testing_experiment


class EnrollUserToPreAlphaTestingExperimentTests(TestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()

    def test_enroll_user_to_prealpha_testing_experiment_happy_path(self):
        with self.assertNoLogs():
            enroll_user_to_prealpha_testing_experiment(self.user)

        self.assertTrue(
            PreAlphaUserTestingExperiment.objects.filter(
                user=self.user,
                experiment_config__experiment_tag=ER_001_PRE_ALPHA_USER_TESTING_TAG,
            ).exists()
        )

        self.assertTrue(
            ExperimentConfig.objects.filter(
                experiment_tag=ER_001_PRE_ALPHA_USER_TESTING_TAG,
                required_user_population=200,
                selection_type=EXPERIMENT_SELECTION_TYPE_FFS,
                is_active=True,
            ).exists()
        )

    def test_enroll_user_to_prealpha_testing_experiment_inactive_experiment(self):
        experiment_config = ExperimentConfigFactory.create(
            experiment_tag=ER_001_PRE_ALPHA_USER_TESTING_TAG,
            required_user_population=1,
            selection_type=1,
            experiment_duration=None,
            meta_data={},
            is_active=False,
        )

        with self.assertLogs() as logs:
            enroll_user_to_prealpha_testing_experiment(self.user)

        self.assertEqual(len(logs.records), 1)
        self.assertEqual(
            logs.records[0].message,
            "uia_backend::experiments::utils::enroll_user_to_prealpha_testing_experiment:: "
            "Experiment is not active.",
        )
        self.assertEqual(
            logs.records[0].experiment_config_id, str(experiment_config.id)
        )
        self.assertEqual(
            logs.records[0].experiment_tag, ER_001_PRE_ALPHA_USER_TESTING_TAG
        )
        self.assertEqual(logs.records[0].levelname, "WARNING")
        self.assertFalse(
            PreAlphaUserTestingExperiment.objects.filter(
                user=self.user,
                experiment_config__experiment_tag=ER_001_PRE_ALPHA_USER_TESTING_TAG,
            ).exists()
        )

    def test_enroll_user_to_prealpha_testing_experiment_experiment_reached_capacity(
        self,
    ):
        experiment_config = ExperimentConfigFactory.create(
            experiment_tag=ER_001_PRE_ALPHA_USER_TESTING_TAG,
            required_user_population=0,
            selection_type=1,
            experiment_duration=None,
            meta_data={},
            is_active=True,
        )

        with self.assertLogs() as logs:
            enroll_user_to_prealpha_testing_experiment(self.user)

        self.assertEqual(len(logs.records), 1)
        self.assertEqual(
            logs.records[0].message,
            "uia_backend::experiments::utils::enroll_user_to_prealpha_testing_experiment:: "
            "Experiment has reached capacity.",
        )
        self.assertEqual(
            logs.records[0].experiment_config_id, str(experiment_config.id)
        )
        self.assertEqual(
            logs.records[0].experiment_tag, ER_001_PRE_ALPHA_USER_TESTING_TAG
        )
        self.assertEqual(logs.records[0].capacity, 0)
        self.assertEqual(logs.records[0].levelname, "WARNING")
        self.assertFalse(
            PreAlphaUserTestingExperiment.objects.filter(
                user=self.user,
                experiment_config__experiment_tag=ER_001_PRE_ALPHA_USER_TESTING_TAG,
            ).exists()
        )
