from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FriendshipConfig(AppConfig):
    name = "uia_backend.friendship"
    verbose_name = _("Friendships")
    
