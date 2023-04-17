from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    name = "uia_backend.accounts"
    verbose_name = _("Accounts")
