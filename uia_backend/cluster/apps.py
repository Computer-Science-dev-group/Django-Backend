from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ClusterConfig(AppConfig):
    name = "uia_backend.cluster"
    verbose_name = _("Cluster")
