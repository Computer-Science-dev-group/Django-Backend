from collections.abc import Sequence
from typing import Any

from django.contrib.auth.models import Group
from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework import exceptions, permissions

from uia_backend.accounts.models import CustomUser as User


def assign_object_permissions(
    permissions: Sequence[str], assignee: User | Group, obj: Any
) -> None:
    """Assign object permissions."""

    for permission in permissions:
        assign_perm(permission, assignee, obj)


def unassign_object_permissions(
    permissions: Sequence[str], assignee: User | Group, obj: Any
) -> None:
    """Unassign object permissions."""

    for permission in permissions:
        remove_perm(permission, assignee, obj)


def check_object_permissions(
    permissions: Sequence[str], assignee: User, obj: Any = None
) -> bool:
    """Check that an object has a sequence of permissions."""
    checker = ObjectPermissionChecker(assignee)

    for permission in permissions:
        has_permission = (
            checker.has_perm(permission, obj) if obj else assignee.has_perm(permission)
        )
        print(f"{permission} {obj}")
        if has_permission is False:
            return False
    return True


class CustomAccessPermission(permissions.DjangoObjectPermissions):
    def get_required_permissions(self, method: str, model_cls: Any = None) -> list[str]:
        if method not in self.perms_map.keys():
            raise exceptions.MethodNotAllowed(method)

        return self.perms_map[method]

    def has_permission(self, request, view):
        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, "_ignore_model_permissions", False):
            return True

        if not request.user or (
            not request.user.is_authenticated and self.authenticated_users_only
        ):
            return False

        return True

    def has_object_permission(self, request, view, obj) -> bool:
        # authentication checks have already executed via has_permission
        user = request.user
        perms = self.get_required_permissions(method=request.method)
        return check_object_permissions(perms, user, obj)
