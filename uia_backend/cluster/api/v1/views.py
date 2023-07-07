from typing import Any

from django.db import transaction
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import filters, generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response

from config.settings.base import CACHE_DURATION
from uia_backend.cluster.api.v1.permissions import (
    ClusterInvitationObjectPermission,
    ClusterMembersObjectPermission,
    ClusterObjectPermission,
    InternalClusterProtectionPermission,
)
from uia_backend.cluster.api.v1.serializers import (
    ClusterInvitationSerializer,
    ClusterMembershipSerializer,
    ClusterSerializer,
)
from uia_backend.cluster.constants import (
    ADD_CLUSTER_MEMBER_PERMISSION,
    REMOVE_CLUSTER_MEMBER_PERMISSION,
    UPDATE_CLUSTER_PERMISSION,
    VIEW_CLUSTER_PERMISSION,
)
from uia_backend.cluster.models import Cluster, ClusterInvitation, ClusterMembership
from uia_backend.libs.permissions import unassign_object_permissions


class ClusterListCreateAPIView(generics.ListCreateAPIView):
    """List/Create clusters API View."""

    serializer_class = ClusterSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["title"]

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 200,
                    "data": [
                        {
                            "id": "string",
                            "title": "string",
                            "description": "string",
                            "icon": "string",
                            "created_by": "string",
                            "is_default": False,
                        },
                        {
                            "id": "00877a65-7dff-403b-acad-c0f37af6bc42",
                            "title": "string",
                            "description": "string",
                            "icon": "path/file.img",
                            "created_by": "string",
                            "is_default": False,
                        },
                    ],
                },
            )
        ]
    )
    @method_decorator(cache_page(CACHE_DURATION))
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    @transaction.atomic()
    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 201,
                    "data": {
                        "id": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "title": "string",
                        "description": "string",
                        "icon": "path/file.img",
                        "created_by": "string",
                        "is_default": False,
                    },
                },
            )
        ]
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().post(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet:
        """Get users clusters."""
        return self.request.user.cluster_member_set.all()

    def perform_create(self, serializer: ClusterSerializer) -> None:
        serializer.save(created_by=self.request.user)


class ClusterDetailAPIView(generics.RetrieveUpdateAPIView):
    """Retrieve/Update a cluster API View."""

    serializer_class = ClusterSerializer
    permission_classes = [permissions.IsAuthenticated, ClusterObjectPermission]

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 200,
                    "data": {
                        "id": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "title": "string",
                        "description": "string",
                        "icon": "path/image.png",
                        "created_by": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "is_default": False,
                    },
                },
            )
        ]
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 200,
                    "data": {
                        "id": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "title": "string",
                        "description": "string",
                        "icon": "path/image.png",
                        "created_by": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "is_default": False,
                    },
                },
            )
        ]
    )
    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().put(request, *args, **kwargs)

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 200,
                    "data": {
                        "id": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "title": "string",
                        "description": "string",
                        "icon": "path/image.png",
                        "created_by": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "is_default": False,
                    },
                },
            )
        ]
    )
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().patch(request, *args, **kwargs)

    def get_object(self) -> Cluster:
        cluster = get_object_or_404(
            self.request.user.cluster_member_set, id=self.kwargs["cluster_id"]
        )
        self.check_object_permissions(request=self.request, obj=cluster)
        return cluster


class ClusterMembershipListAPIView(generics.ListAPIView):
    serializer_class = ClusterMembershipSerializer
    permission_classes = [permissions.IsAuthenticated, ClusterMembersObjectPermission]
    queryset = ClusterMembership.objects.all()

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 200,
                    "data": [
                        {
                            "id": "f88678e4-3491-402b-b3e5-bc56ed81b760",
                            "user": {
                                "first_name": "string",
                                "last_name": "string",
                                "profile_picture": "path/image.png",
                                "cover_photo": "path/image.png",
                                "phone_number": "string",
                                "display_name": "string",
                                "year_of_graduation": "1990",
                                "department": "string",
                                "faculty": "Science",
                                "bio": "string",
                                "gender": "string",
                                "date_of_birth": "string",
                            },
                        }
                    ],
                },
            )
        ]
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet:
        # Apply cluster permissions
        cluster = self.get_object()
        return super().get_queryset().filter(cluster=cluster)

    def get_object(self) -> Any:
        cluster = get_object_or_404(
            self.request.user.cluster_member_set, id=self.kwargs["cluster_id"]
        )
        self.check_object_permissions(request=self.request, obj=cluster)
        return cluster


class ClusterMembersDetailAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = ClusterMembershipSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        ClusterMembersObjectPermission,
    ]

    def get_object(self) -> ClusterMembership:
        membership_record = get_object_or_404(
            ClusterMembership.objects.select_related("cluster"),
            cluster_id=self.kwargs["cluster_id"],
            id=self.kwargs["membership_id"],
        )

        # if its an internal cluster apply the InternalClusterProtectionPermission
        # NOTE: This is a crud fix to ensure users can not leave internal clusters
        if membership_record.cluster.internal_cluster is not None:
            self.permission_classes = (
                permissions.IsAuthenticated,
                InternalClusterProtectionPermission,
            )
            self.check_object_permissions(
                request=self.request, obj=membership_record.cluster
            )

        if membership_record.user == self.request.user:
            # we want to ensure that user can delete their own membership data
            return membership_record

        self.check_object_permissions(
            request=self.request, obj=membership_record.cluster
        )
        return membership_record

    def perform_destroy(self, instance: ClusterMembership) -> None:
        # remove all cluster permissions from member before deleting
        unassign_object_permissions(
            permissions=[
                VIEW_CLUSTER_PERMISSION,
                UPDATE_CLUSTER_PERMISSION,
                ADD_CLUSTER_MEMBER_PERMISSION,
                REMOVE_CLUSTER_MEMBER_PERMISSION,
            ],
            assignee=instance.user,
            obj=instance.cluster,
        )
        instance.delete()


class ClusterInvitationListAPIView(generics.ListCreateAPIView):
    """List/Create Cluster Invitation API View."""

    serializer_class = ClusterInvitationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        ClusterInvitationObjectPermission,
    ]
    queryset = ClusterInvitation.objects.all()

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 201,
                    "data": {
                        "id": "b60e8eed-e0bc-4530-8b60-70eaaee36ed5",
                        "cluster": "e9a39164-0bf8-42ac-aff9-6620bb9019fb",
                        "status": 0,
                        "duration": 10,
                        "created_by": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "user": "ab9c9db6-5b22-4e2c-8f1e-f3f6480710a8",
                    },
                },
            )
        ]
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # ensure object permission check runs
        self.get_object()
        return super().post(request, *args, **kwargs)

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 200,
                    "data": {
                        "id": "b60e8eed-e0bc-4530-8b60-70eaaee36ed5",
                        "cluster": "e9a39164-0bf8-42ac-aff9-6620bb9019fb",
                        "status": 0,
                        "duration": 10,
                        "created_by": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "user": "ab9c9db6-5b22-4e2c-8f1e-f3f6480710a8",
                    },
                },
            )
        ]
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[ClusterInvitation]:
        cluster = self.get_object()
        return super().get_queryset().filter(cluster=cluster)

    def get_object(self) -> Cluster:
        cluster = get_object_or_404(
            self.request.user.cluster_member_set, id=self.kwargs["cluster_id"]
        )
        self.check_object_permissions(request=self.request, obj=cluster)
        return cluster

    def perform_create(self, serializer: ClusterInvitationSerializer) -> None:
        serializer.save(
            created_by=self.request.user,
            cluster_id=self.kwargs["cluster_id"],
        )


class ClusterInvitationDetailAPIView(generics.RetrieveUpdateAPIView):
    """Retrieve/Update a Cluster Invitation API View."""

    serializer_class = ClusterInvitationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        ClusterInvitationObjectPermission,
    ]
    http_method_names = ["get", "patch"]

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 200,
                    "data": {
                        "id": "b60e8eed-e0bc-4530-8b60-70eaaee36ed5",
                        "cluster": "e9a39164-0bf8-42ac-aff9-6620bb9019fb",
                        "status": 0,
                        "duration": 10,
                        "created_by": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "user": "ab9c9db6-5b22-4e2c-8f1e-f3f6480710a8",
                    },
                },
            )
        ]
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 200,
                    "data": {
                        "id": "b60e8eed-e0bc-4530-8b60-70eaaee36ed5",
                        "cluster": "e9a39164-0bf8-42ac-aff9-6620bb9019fb",
                        "status": 0,
                        "duration": 10,
                        "created_by": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "user": "ab9c9db6-5b22-4e2c-8f1e-f3f6480710a8",
                    },
                },
            )
        ]
    )
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().patch(request, *args, **kwargs)

    def get_object(self) -> ClusterInvitation:
        invitation_record = get_object_or_404(
            ClusterInvitation.objects.select_related("cluster"),
            cluster_id=self.kwargs["cluster_id"],
            id=self.kwargs["invitation_id"],
        )

        self.check_object_permissions(
            request=self.request, obj=invitation_record.cluster
        )
        return invitation_record


class UserClusterInvitationListAPIView(generics.ListAPIView):
    serializer_class = ClusterInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    " code": 200,
                    "data": [
                        {
                            "id": "b60e8eed-e0bc-4530-8b60-70eaaee36ed5",
                            "cluster": "e9a39164-0bf8-42ac-aff9-6620bb9019fb",
                            "status": 1,
                            "duration": 10,
                            "created_by": "00877a65-7dff-403b-acad-c0f37af6bc42",
                            "user": "ab9c9db6-5b22-4e2c-8f1e-f3f6480710a8",
                        },
                    ],
                },
            )
        ]
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet:
        return self.request.user.cluster_invitations.all()


class UserClusterInvitationDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ClusterInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch"]

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 200,
                    "data": {
                        "id": "b60e8eed-e0bc-4530-8b60-70eaaee36ed5",
                        "cluster": "e9a39164-0bf8-42ac-aff9-6620bb9019fb",
                        "status": 0,
                        "duration": 10,
                        "created_by": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "user": "ab9c9db6-5b22-4e2c-8f1e-f3f6480710a8",
                    },
                },
            )
        ]
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example",
                response_only=True,
                value={
                    "status": "Success",
                    "code": 200,
                    "data": {
                        "id": "b60e8eed-e0bc-4530-8b60-70eaaee36ed5",
                        "cluster": "e9a39164-0bf8-42ac-aff9-6620bb9019fb",
                        "status": 0,
                        "duration": 10,
                        "created_by": "00877a65-7dff-403b-acad-c0f37af6bc42",
                        "user": "ab9c9db6-5b22-4e2c-8f1e-f3f6480710a8",
                    },
                },
            )
        ]
    )
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(
            self.request.user.cluster_invitations, id=self.kwargs["invitation_id"]
        )
