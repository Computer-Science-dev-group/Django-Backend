# Experiment selection options
# ------------------------------------------------------------------------------
EXPERIMENT_SELECTION_TYPE_FFS = 0  # first come first serve
EXPERIMENT_SELECTION_TYPE_URD = 1  # Unifrom random distribution

EXPERIMENT_SELECTION_TYPE_CHOICES = [
    (EXPERIMENT_SELECTION_TYPE_FFS, "First-come First-serve"),
    (EXPERIMENT_SELECTION_TYPE_URD, "Uniform Random Distribution"),
]


# Experiment tags
# ------------------------------------------------------------------------------
ER_001_PRE_ALPHA_USER_TESTING_TAG = "ER001_Pre_alpha_user_testing"
ER_001_CONFIG = {
    "required_user_population": 200,
    "selection_type": EXPERIMENT_SELECTION_TYPE_FFS,
    "is_active": True,
}
