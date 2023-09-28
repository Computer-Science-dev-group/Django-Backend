from logging import getLogger
from typing import Any

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.db.models.query import QuerySet
from django.db.utils import Error
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response

from uia_backend.accounts.api.v1.queries import USER_FEED_QUERY
from uia_backend.accounts.api.v1.serializers import (
    ChangePasswordSerializer,
    EmailVerificationSerializer,
    FollowerSerializer,
    FollowingSerializer,
    FriendshipInvitationSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    RestPasswordRequestSerializer,
    UserFriendShipSettingsSerializer,
    UserGenericSettingsSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    VerifyResetPasswordOTPSerializer,
)
from uia_backend.accounts.api.v1.throttles import (
    ChangePassswordThrottle,
    PasswordRestThrottle,
)
from uia_backend.accounts.models import (
    CustomUser,
    Follows,
    FriendShipInvitation,
    UserFriendShipSettings,
    UserGenericSettings,
)
from uia_backend.cluster.constants import VIEW_CLUSTER_PERMISSION
from uia_backend.experiments.constants import ER_001_PRE_ALPHA_USER_TESTING_TAG
from uia_backend.experiments.models import (
    ExperimentConfig,
    PreAlphaUserTestingExperiment,
)
from uia_backend.messaging.api.v1.serializers import PostSerializer
from uia_backend.messaging.models import Post
from uia_backend.notification import constants as notification_constants
from uia_backend.notification.utils.notification_senders import Notifier

logger = getLogger()


class UserRegistrationAPIView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @transaction.atomic()
    def post(self, request: Request, *args: Any, **kwargs: dict[str, Any]) -> Response:
        # NOTE: (Joseph) we need to remove this code when done with this experiment
        # before doing any data validation lets check if ER001 is still active
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
        else:
            # next we need to check if experiment has reached its capacity
            enrolled_user_count = PreAlphaUserTestingExperiment.objects.filter(
                experiment_config=er_config
            ).count()
            if er_config.required_user_population <= enrolled_user_count:
                return Response(
                    data={
                        "detail": "Sorry we cant register your account as pre-alpha testing is no longer active"
                    },
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )

        return super().post(request, *args, **kwargs)


# NOTE: For now lets use a API request for this later we can build a nice looking template
# NOTE: We also have to figure out a way to handle verification for web
# (we may want to redirect to the web app or something)
class EmailVerificationAPIView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.AllowAny]

    @transaction.atomic()
    def get(self, request: Request, signature: str) -> Response:
        serializer = self.get_serializer(data={"signature": signature})
        is_valid = serializer.is_valid()
        status_code = status.HTTP_400_BAD_REQUEST
        if is_valid:
            status_code = status.HTTP_200_OK
            serializer.save()

        return render(
            request,
            "email_verification.html",
            context={"is_valid": is_valid},
            status=status_code,
        )


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    """Retrieve/Update authenticated users profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "put"]

    def get_object(self) -> CustomUser:
        return self.request.user


class ChangePasswordAPIView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ChangePassswordThrottle]
    http_method_names = ["put"]

    def get_object(self) -> Any:
        return self.request.user


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        """User login view."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # NOTE: we can send a task here to store login attempt
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class ResetPasswordRequestAPIView(generics.CreateAPIView):
    serializer_class = RestPasswordRequestSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordRestThrottle]


class VerifyResetPasswordAPIView(generics.GenericAPIView):
    """View for verifying a password reset attempt using an OTP."""

    serializer_class = VerifyResetPasswordOTPSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["post"]

    def post(self, request: Request) -> Response:
        """Verify password view."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ResetPasswordAPIView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["post"]

    def post(self, request: Request) -> Response:
        """Reset password view."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserProfileListView(generics.ListAPIView):
    """List profiles of active all user."""

    queryset = CustomUser.objects.filter(is_active=True)
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["first_name", "last_name", "display_name"]


class UserProfileDetailAPIView(generics.RetrieveAPIView):
    """Retrieve a users profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> CustomUser:
        return get_object_or_404(
            klass=CustomUser,
            id=self.kwargs["user_id"],
            is_active=True,
        )


class FriendShipInvitationListAPIView(generics.ListCreateAPIView):
    serializer_class = FriendshipInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status"]
    ordering_fields = ["created_datetime"]
    ordering = ["-created_datetime"]

    def get_queryset(self) -> QuerySet[FriendShipInvitation]:
        return FriendShipInvitation.objects.filter(
            Q(created_by=self.request.user) | Q(user=self.request.user)
        ).select_related("user", "created_by")

    def perform_create(self, serializer: FriendshipInvitationSerializer) -> None:
        serializer.save(created_by=self.request.user)


class FriendShipInvitationDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = FriendshipInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch"]

    def get_queryset(self) -> QuerySet[FriendShipInvitation]:
        return FriendShipInvitation.objects.filter(
            Q(created_by=self.request.user) | Q(user=self.request.user)
        ).select_related("user", "created_by")

    def get_object(self) -> FriendShipInvitation:
        """Get object"""
        try:
            record = FriendShipInvitation.objects.filter(
                Q(created_by=self.request.user) | Q(user=self.request.user)
            ).get(id=self.kwargs["pk"])
        except FriendShipInvitation.DoesNotExist:
            raise Http404

        return record


class UserFriendShipsListAPIView(generics.ListAPIView):
    serializer_class = UserFriendShipSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_blocked"]
    search_fields = ["friendship__users__first_name", "friendship__users__last_name"]
    ordering_fields = [
        "created_datetime",
        "friendship__users__first_name",
        "friendship__users__last_name",
    ]
    ordering = ["-created_datetime"]

    def get_queryset(self) -> QuerySet[UserFriendShipSettings]:
        return UserFriendShipSettings.objects.filter(user=self.request.user)


class UserFriendShipsDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserFriendShipSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[UserFriendShipSettings]:
        return UserFriendShipSettings.objects.filter(user=self.request.user)

    def perform_destroy(self, instance: UserFriendShipSettings) -> None:
        instance.friendship.delete()

    def get_object(self) -> UserFriendShipSettings:
        """Get object"""
        return get_object_or_404(
            UserFriendShipSettings,
            id=self.kwargs["pk"],
            user=self.request.user,
        )


# NOTE (Joseph): This view only work on posgres DB (We need to find a better implementation)
class UserFeedAPIView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_datetime"]
    ordering = ["-created_datetime"]

    def get_queryset(self) -> QuerySet[Post]:
        """Return the queryset of posts for the user's feed."""

        try:
            # NOTE: Be careful to not change the arrangement of the params without
            # effecting the change in the SQL Query
            with transaction.atomic():
                query = Post.objects.filter(
                    id__in=RawSQL(
                        sql=USER_FEED_QUERY,
                        params=[
                            self.request.user.id,
                            VIEW_CLUSTER_PERMISSION,
                            settings.REST_FRAMEWORK["PAGE_SIZE"],
                        ],
                    )
                )
        except Error as error:
            # let catch everything just in case somthing breaks in the query
            # so we dont return noting to the user lets return their own posts
            logger.exception(
                "uia_backend::accounts::api::v1::views::UserFeedAPIView::get_queryset:: "
                "A error occured while retrieveing users feed.",
                extra={
                    "user_id": self.request.user.id,
                    "query": USER_FEED_QUERY,
                    "error": str(error),
                },
            )

            query = Post.objects.filter(
                created_by=self.request.user,
            )

        return query


class UserFollowerListAPIView(generics.ListAPIView):
    """List a users followers."""

    serializer_class = FollowerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = [
        "user_from__first_name",
        "user_from__last_name",
        "user_from__display_name",
    ]
    ordering_fields = ["created_datetime", "-created_datetime"]
    ordering = ["-created_datetime"]

    def get_queryset(self) -> QuerySet[Follows]:
        user_id = self.request.query_params.get("user_id")

        if user_id:
            query = Follows.objects.filter(user_to_id=user_id)
        else:
            query = Follows.objects.filter(user_to=self.request.user)

        return query


class UserFollowingListAPIView(generics.ListCreateAPIView):
    """List/create users authenticated user is following."""

    serializer_class = FollowingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = [
        "user_to__first_name",
        "user_to__last_name",
        "user_to__display_name",
    ]
    ordering_fields = ["created_datetime", "-created_datetime"]
    ordering = ["-created_datetime"]

    def get_queryset(self) -> QuerySet[Follows]:
        user_id = self.request.query_params.get("user_id")

        if user_id:
            query = Follows.objects.filter(user_from_id=user_id)
        else:
            query = Follows.objects.filter(user_from=self.request.user)
        return query

    def perform_create(self, serializer: FollowingSerializer) -> None:
        follow_record = serializer.save(user_from=self.request.user)

        if (
            hasattr(follow_record.user_to, "settings")
            and follow_record.user_to.settings.notification["follow"]
        ):
            # notify user that they have been followed
            event_data = {
                "recipients": [follow_record.user_to],
                "verb": "followed",
                "metadata": dict(serializer.to_representation(instance=follow_record)),
                "actor": follow_record.user_from,
                "target": follow_record.user_to,
            }

            notifier = Notifier(
                event=notification_constants.FOLLOW_USER_NOTIFICATION, data=event_data
            )
            notifier.send_notification()


class UserFollowingDetailAPIView(generics.DestroyAPIView):
    """Unfollow a user."""

    serializer_class = FollowingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> Follows:
        return get_object_or_404(
            Follows, user_from=self.request.user, user_to_id=self.kwargs["user_id"]
        )

    def perform_destroy(self, instance: Follows) -> None:
        """Unfollow a user."""

        if (
            hasattr(instance.user_to, "settings")
            and instance.user_to.settings.notification["follow"]
        ):
            # notify user that they have been followed
            event_data = {
                "recipients": [instance.user_to],
                "verb": "un-followed",
                "metadata": dict(
                    FollowingSerializer().to_representation(instance=instance)
                ),
                "actor": instance.user_from,
                "target": instance.user_to,
            }

            notifier = Notifier(
                event=notification_constants.UNFOLLOW_USER_NOTIFICATION, data=event_data
            )
            notifier.send_notification()
        return super().perform_destroy(instance)


class UserGenericSettingsAPIView(generics.RetrieveUpdateAPIView):
    """Retrieve/Update user settings."""

    serializer_class = UserGenericSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch"]

    def get_object(self) -> UserGenericSettings:
        if not hasattr(self.request.user, "settings"):
            logger.error(
                "uia_backend.accounts.api.v1.views.get_object:: User does not have UserGenericSettings record.",
                extra={"user_id": self.request.user.id},
            )
            raise Http404
        return self.request.user.settings
