import django_filters

from uia_backend.accounts.models import Follows


class UserFollowersFilterSet(django_filters.FilterSet):
    class Meta:
        model = Follows
        fields = [""]
