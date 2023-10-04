import uuid
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import urlencode

from django.test import override_settings
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart
from django.urls import reverse
from rest_framework.test import APITestCase

from tests.accounts.test_models import UserModelFactory
from tests.cluster.test_models import (
    ClusterFactory,
    ClusterInvitationFactory,
    ClusterMembershipFactory,
    InternalClusterFactory,
)
from uia_backend.accounts.api.v1.serializers import ProfileSerializer
from uia_backend.cluster.api.v1.serializers import ClusterInvitationSerializer
from uia_backend.cluster.constants import (
    ADD_CLUSTER_MEMBER_PERMISSION,
    REMOVE_CLUSTER_MEMBER_PERMISSION,
    UPDATE_CLUSTER_PERMISSION,
    VIEW_CLUSTER_PERMISSION,
)
from uia_backend.cluster.models import Cluster, ClusterInvitation
from uia_backend.libs.permissions import (
    assign_object_permissions,
    check_object_permissions,
    unassign_object_permissions,
)
from uia_backend.libs.testutils import get_test_image_file
from uia_backend.notification import constants as notification_constants


class ClusterListCreateAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com", is_active=True)
        self.url = reverse("cluster_api_v1:list_create_cluster")
        self.client.force_authenticate(user=self.user)

    def test_list_user_clusters_case_1(self):
        """Test list users cluster when user has cluster."""
        user_cluster = ClusterFactory.create(
            title="A cluster I joined",
        )
        ClusterMembershipFactory.create(cluster=user_cluster, user=self.user)

        internal_cluster = ClusterFactory.create(
            title="Global",
            internal_cluster=InternalClusterFactory.create(name="global"),
        )
        ClusterMembershipFactory.create(cluster=internal_cluster, user=self.user)

        # some cluster that user is not part of
        ClusterFactory.create(title="Unknown")

        response = self.client.get(path=self.url)
        expected_data = {
            "status": "Success",
            "code": 200,
            "count": 2,
            "next": None,
            "previous": None,
            "data": [
                {
                    "id": str(internal_cluster.id),
                    "title": internal_cluster.title,
                    "description": internal_cluster.description,
                    "icon": internal_cluster.icon,
                    "created_by": None,
                    "is_default": True,
                },
                {
                    "id": str(user_cluster.id),
                    "title": user_cluster.title,
                    "description": user_cluster.description,
                    "icon": user_cluster.icon,
                    "created_by": None,
                    "is_default": False,
                },
            ],
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_list_user_clusters_case_2(self):
        """Test list users cluster when user has no cluster."""
        # Disable cache for this test
        with override_settings(
            CACHES={
                "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
            }
        ):
            # some cluster that user is not part of
            ClusterFactory.create(title="Unknown")

            response = self.client.get(path=self.url)
            expected_data = {
                "status": "Success",
                "code": 200,
                "count": 0,
                "next": None,
                "previous": None,
                "data": [],
            }
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), expected_data)

    def test_list_user_clusters_with_matching_result(self):
        """Test list users cluster when user has matching result with the query parameter."""
        user_cluster = ClusterFactory.create(title="A cluster I joined")
        ClusterMembershipFactory.create(cluster=user_cluster, user=self.user)

        internal_cluster = ClusterFactory.create(
            title="Global",
            internal_cluster=InternalClusterFactory.create(name="global"),
        )
        ClusterMembershipFactory.create(cluster=internal_cluster, user=self.user)

        # some cluster that user is not part of
        user_cluster_two = ClusterFactory.create(title="A new test")
        ClusterMembershipFactory.create(cluster=user_cluster_two, user=self.user)
        query_params = {
            "search": "A clu",
        }
        url_with_params = f"{self.url}?{urlencode(query_params)}"
        response = self.client.get(path=url_with_params)
        expected_data = {
            "status": "Success",
            "code": 200,
            "count": 1,
            "next": None,
            "previous": None,
            "data": [
                {
                    "id": str(user_cluster.id),
                    "title": user_cluster.title,
                    "description": user_cluster.description,
                    "icon": user_cluster.icon,
                    "created_by": None,
                    "is_default": False,
                },
            ],
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_list_cluster_with_no_results(self):
        """Test list cluster with no results."""
        user_cluster = ClusterFactory.create(title="Unknown")
        ClusterMembershipFactory.create(cluster=user_cluster, user=self.user)
        query_params = {
            "search": "Not Existing",
        }
        url_with_params = f"{self.url}?{urlencode(query_params)}"
        expected_data = {
            "count": 0,
            "next": None,
            "previous": None,
            "status": "Success",
            "code": 200,
            "data": [],
        }
        response = self.client.get(path=url_with_params)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)

    def test_create_cluster_sucessfully(self):
        data = {
            "title": "string",
            "description": "string",
            "icon": get_test_image_file(name="icon.png"),
        }

        response = self.client.post(
            path=self.url,
            data=encode_multipart(data=data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, 201)

        cluster = Cluster.objects.first()
        self.assertIsNotNone(cluster)
        expected_response_data = {
            "status": "Success",
            "code": 201,
            "data": {
                "id": str(cluster.id),
                "title": "string",
                "description": "string",
                "icon": f"http://testserver/media/clusters/{cluster.id}/icon/icon.png",
                "created_by": str(self.user.id),
                "is_default": False,
            },
        }

        self.assertDictEqual(expected_response_data, response.json())

        creator_permissions = [
            VIEW_CLUSTER_PERMISSION,
            UPDATE_CLUSTER_PERMISSION,
            ADD_CLUSTER_MEMBER_PERMISSION,
            REMOVE_CLUSTER_MEMBER_PERMISSION,
        ]

        self.assertTrue(
            check_object_permissions(
                permissions=creator_permissions, assignee=self.user, obj=cluster
            )
        )


class ClusterDetailAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com", is_active=True)
        self.client.force_authenticate(user=self.user)
        self.cluster = ClusterFactory.create(title="A cluster I joined")
        ClusterMembershipFactory.create(cluster=self.cluster, user=self.user)
        assign_object_permissions(
            permissions=[VIEW_CLUSTER_PERMISSION, UPDATE_CLUSTER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

    def test_retrieve_cluster__case_1(self):
        """Test to show that a cluster member can retrieve a clusters."""

        url = reverse(
            "cluster_api_v1:retrieve_update_cluster", args=[str(self.cluster.id)]
        )
        expected_data = {
            "status": "Success",
            "code": 200,
            "data": {
                "id": str(self.cluster.id),
                "title": self.cluster.title,
                "description": self.cluster.description,
                "icon": self.cluster.icon,
                "created_by": None,
                "is_default": False,
            },
        }

        response = self.client.get(path=url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)

    def test_retrieve_cluster__case_2(self):
        """Test to show that a non cluster member can not retrieve a cluster."""

        cluster = ClusterFactory.create(title="Some strange cluster.")
        url = reverse("cluster_api_v1:retrieve_update_cluster", args=[str(cluster.id)])

        expected_data = {
            "status": "Error",
            "code": 404,
            "data": {"detail": "Not found."},
        }

        response = self.client.get(path=url)
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.json(), expected_data)

    def test_retrieve_cluster__case_3(self):
        """Test retrieving non-existent cluster."""

        url = reverse(
            "cluster_api_v1:retrieve_update_cluster", args=[str(uuid.uuid4())]
        )

        expected_data = {
            "status": "Error",
            "code": 404,
            "data": {"detail": "Not found."},
        }

        response = self.client.get(path=url)
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.json(), expected_data)

    def test_update_cluster__case_1(self):
        """Test to ensure that group memebers with update permission can update a cluster."""

        url = reverse(
            "cluster_api_v1:retrieve_update_cluster", args=[str(self.cluster.id)]
        )
        expected_data = {
            "status": "Success",
            "code": 200,
            "data": {
                "id": str(self.cluster.id),
                "title": "In to the wind",
                "description": "Everything Goes.",
                "icon": f"http://testserver/media/clusters/{self.cluster.id}/icon/my-Icon.png",
                "created_by": None,
                "is_default": False,
            },
        }

        request_data = {
            "title": "In to the wind",
            "description": "Everything Goes.",
            "icon": get_test_image_file(name="my-Icon.png"),
        }

        response = self.client.put(
            path=url,
            data=encode_multipart(data=request_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)

    def test_update_cluster__case_2(self):
        """Test that member without update permission is unable to update cluster perimission."""

        # remove user's update permission
        unassign_object_permissions(
            permissions=[UPDATE_CLUSTER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

        url = reverse(
            "cluster_api_v1:retrieve_update_cluster", args=[str(self.cluster.id)]
        )
        expected_data = {
            "status": "Error",
            "code": 403,
            "data": {"detail": "You do not have permission to perform this action."},
        }

        request_data = {
            "title": "In to the wind",
            "description": "Everything Goes.",
            "icon": get_test_image_file(name="my-Icon.png"),
        }

        response = self.client.put(
            path=url,
            data=encode_multipart(data=request_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.json(), expected_data)

    def test_update_cluster__case_3(self):
        """Test that non-member user can not update a cluster."""

        user = UserModelFactory.create(email="miscope@missisipi.com")
        self.client.force_authenticate(user=user)

        url = reverse(
            "cluster_api_v1:retrieve_update_cluster", args=[str(self.cluster.id)]
        )
        expected_data = {
            "status": "Error",
            "code": 404,
            "data": {"detail": "Not found."},
        }

        request_data = {
            "title": "In to the wind",
            "description": "Everything Goes.",
            "icon": get_test_image_file(name="my-Icon.png"),
        }

        response = self.client.put(
            path=url,
            data=encode_multipart(data=request_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.json(), expected_data)


class ClusterMembershipListAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com", is_active=True)
        self.client.force_authenticate(user=self.user)
        self.cluster = ClusterFactory.create(title="A cluster I joined")
        self.membership = ClusterMembershipFactory.create(
            cluster=self.cluster, user=self.user
        )
        assign_object_permissions(
            permissions=[
                VIEW_CLUSTER_PERMISSION,
                ADD_CLUSTER_MEMBER_PERMISSION,
                REMOVE_CLUSTER_MEMBER_PERMISSION,
            ],
            assignee=self.user,
            obj=self.cluster,
        )

    def test_list_cluster_members__case_1(self):
        """Test Retrieving cluster members when user has view permission."""

        member_1 = UserModelFactory.create(email="member_1@example.com")
        membership_1 = ClusterMembershipFactory.create(
            cluster=self.cluster, user=member_1
        )

        expected_data = {
            "status": "Success",
            "code": 200,
            "count": 2,
            "next": None,
            "previous": None,
            "data": [
                {
                    "id": str(membership_1.id),
                    "user": dict(
                        ProfileSerializer().to_representation(instance=member_1)
                    ),
                },
                {
                    "id": str(self.membership.id),
                    "user": dict(
                        ProfileSerializer().to_representation(instance=self.user)
                    ),
                },
            ],
        }

        url = reverse(
            "cluster_api_v1:list_cluster_members", args=[str(self.cluster.id)]
        )

        response = self.client.get(path=url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            expected_data,
        )

    def test_list_cluster_members__case_2(self):
        """Test Retrieving cluster members when user does not have view permission."""

        # remove user's view permission
        unassign_object_permissions(
            permissions=[VIEW_CLUSTER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

        expected_data = {
            "status": "Error",
            "code": 403,
            "data": {"detail": "You do not have permission to perform this action."},
        }

        url = reverse(
            "cluster_api_v1:list_cluster_members", args=[str(self.cluster.id)]
        )

        response = self.client.get(path=url)

        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.json(), expected_data)

    def test_list_cluster_members__case_3(self):
        """Test Retrieving cluster members cluster not found."""

        expected_data = {
            "status": "Error",
            "code": 404,
            "data": {"detail": "Not found."},
        }
        url = reverse("cluster_api_v1:list_cluster_members", args=[str(uuid.uuid4())])

        response = self.client.get(path=url)
        self.assertEqual(response.status_code, 404)

        self.assertDictEqual(
            response.json(),
            expected_data,
        )


class ClusterMembersDetailAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com", is_active=True)
        self.client.force_authenticate(user=self.user)
        self.cluster = ClusterFactory.create(title="A cluster I joined")
        self.membership = ClusterMembershipFactory.create(
            cluster=self.cluster, user=self.user
        )
        assign_object_permissions(
            permissions=[
                VIEW_CLUSTER_PERMISSION,
                ADD_CLUSTER_MEMBER_PERMISSION,
                REMOVE_CLUSTER_MEMBER_PERMISSION,
            ],
            assignee=self.user,
            obj=self.cluster,
        )

    def test_retrieve_cluster_member__case_1(self):
        """Test retrieve clutser member when user has view permission."""

        url = reverse(
            "cluster_api_v1:retrieve_delete_cluster_member",
            args=[str(self.cluster.id), str(self.membership.id)],
        )

        expected_data = {
            "status": "Success",
            "code": 200,
            "data": {
                "id": str(self.membership.id),
                "user": dict(ProfileSerializer().to_representation(instance=self.user)),
            },
        }

        response = self.client.get(path=url)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            expected_data,
        )

    def test_retrieve_cluster_member__case_2(self):
        """Test retrieve clutser member when user does not have permission."""

        user = UserModelFactory.create(email="rolex@example.com", is_active=True)
        membership_to_retrieve = ClusterMembershipFactory.create(
            cluster=self.cluster, user=user
        )

        url = reverse(
            "cluster_api_v1:retrieve_delete_cluster_member",
            args=[str(self.cluster.id), str(membership_to_retrieve.id)],
        )

        # remove user's view permission
        unassign_object_permissions(
            permissions=[VIEW_CLUSTER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

        response = self.client.get(path=url)

        expected_data = {
            "status": "Error",
            "code": 403,
            "data": {"detail": "You do not have permission to perform this action."},
        }

        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.json(), expected_data)

    def test_retrieve_cluster_member__case_3_1(self):
        """Test retrieve clutser member invalid cluster id."""

        url = reverse(
            "cluster_api_v1:retrieve_delete_cluster_member",
            args=[str(uuid.uuid4()), str(self.membership.id)],
        )

        expected_data = {
            "status": "Error",
            "code": 404,
            "data": {"detail": "Not found."},
        }

        response = self.client.get(path=url)
        self.assertEqual(response.status_code, 404)

        self.assertDictEqual(
            response.json(),
            expected_data,
        )

    def test_retrieve_cluster_member__case_3_2(self):
        """Test retrieve clutser member invalid user id."""

        url = reverse(
            "cluster_api_v1:retrieve_delete_cluster_member",
            args=[str(self.cluster.id), str(uuid.uuid4())],
        )

        expected_data = {
            "status": "Error",
            "code": 404,
            "data": {"detail": "Not found."},
        }

        response = self.client.get(path=url)
        self.assertEqual(response.status_code, 404)

        self.assertDictEqual(
            response.json(),
            expected_data,
        )

    def test_delete_cluster_member__case_1(self):
        """Test deleting a cluster members when user has remove member permission."""

        user = UserModelFactory.create(email="rolex@example.com", is_active=True)
        membership_to_delete = ClusterMembershipFactory.create(
            cluster=self.cluster, user=user
        )
        permissions_to_check = [
            VIEW_CLUSTER_PERMISSION,
            UPDATE_CLUSTER_PERMISSION,
            ADD_CLUSTER_MEMBER_PERMISSION,
            REMOVE_CLUSTER_MEMBER_PERMISSION,
        ]

        assign_object_permissions(
            permissions=permissions_to_check, assignee=user, obj=self.cluster
        )

        url = reverse(
            "cluster_api_v1:retrieve_delete_cluster_member",
            args=[str(self.cluster.id), str(membership_to_delete.id)],
        )

        response = self.client.delete(path=url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, None)

        self.assertFalse(
            check_object_permissions(
                permissions=permissions_to_check, assignee=user, obj=self.cluster
            )
        )

    def test_delete_cluster_member__case_2(self):
        """Test deleting a cluster member when user does not have remove member permission."""

        user = UserModelFactory.create(email="rolex@example.com", is_active=True)
        membership_to_delete = ClusterMembershipFactory.create(
            cluster=self.cluster, user=user
        )

        url = reverse(
            "cluster_api_v1:retrieve_delete_cluster_member",
            args=[str(self.cluster.id), str(membership_to_delete.id)],
        )

        # remove user's remove cluster member permission
        unassign_object_permissions(
            permissions=[REMOVE_CLUSTER_MEMBER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

        expected_data = {
            "status": "Error",
            "code": 403,
            "data": {"detail": "You do not have permission to perform this action."},
        }

        response = self.client.delete(path=url)

        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.json(), expected_data)

    def test_delete_cluster_member__case_3(self):
        """Test deleting a cluster members record does not exists."""
        url = reverse(
            "cluster_api_v1:retrieve_delete_cluster_member",
            args=[str(self.cluster.id), str(uuid.uuid4())],
        )

        expected_data = {
            "status": "Error",
            "code": 404,
            "data": {"detail": "Not found."},
        }

        response = self.client.delete(path=url)
        self.assertEqual(response.status_code, 404)

        self.assertDictEqual(
            response.json(),
            expected_data,
        )

    def test_delete_cluster_member__case_4(self):
        """Test that a user can delete their own cluster membership with no need to have remove member permission."""

        url = reverse(
            "cluster_api_v1:retrieve_delete_cluster_member",
            args=[str(self.cluster.id), str(self.membership.id)],
        )

        # remove user's remove cluster member permission
        unassign_object_permissions(
            permissions=[REMOVE_CLUSTER_MEMBER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

        response = self.client.delete(path=url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, None)

        permissions_to_check = [
            VIEW_CLUSTER_PERMISSION,
            UPDATE_CLUSTER_PERMISSION,
            ADD_CLUSTER_MEMBER_PERMISSION,
            REMOVE_CLUSTER_MEMBER_PERMISSION,
        ]

        self.assertFalse(
            check_object_permissions(
                permissions=permissions_to_check, assignee=self.user, obj=self.cluster
            )
        )

    def test_delete_cluster_member__case_5(self):
        """Test that a user can not be removed from internal clusters."""
        internal_cluster = InternalClusterFactory.create(name="global")
        self.cluster.internal_cluster = internal_cluster
        self.cluster.save()

        url = reverse(
            "cluster_api_v1:retrieve_delete_cluster_member",
            args=[str(self.cluster.id), str(self.membership.id)],
        )
        response = self.client.delete(path=url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 403,
                "data": {
                    "detail": "You do not have permission to perform this action."
                },
            },
        )

        permissions_to_check = [
            VIEW_CLUSTER_PERMISSION,
            ADD_CLUSTER_MEMBER_PERMISSION,
            REMOVE_CLUSTER_MEMBER_PERMISSION,
        ]

        self.assertTrue(
            check_object_permissions(
                permissions=permissions_to_check, assignee=self.user, obj=self.cluster
            )
        )


class ClusterInvitationListAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com", is_active=True)
        self.client.force_authenticate(user=self.user)
        self.cluster = ClusterFactory.create(title="A cluster I joined")
        self.membership = ClusterMembershipFactory.create(
            cluster=self.cluster, user=self.user
        )
        assign_object_permissions(
            permissions=[
                VIEW_CLUSTER_PERMISSION,
                ADD_CLUSTER_MEMBER_PERMISSION,
                REMOVE_CLUSTER_MEMBER_PERMISSION,
            ],
            assignee=self.user,
            obj=self.cluster,
        )

    def test_list_cluster_invitation__case_1(self):
        """Test list cluster invitation when user has cluster view permission."""
        user_to_invite = UserModelFactory.create(email="maskon@test.com")
        invitation_record = ClusterInvitationFactory.create(
            user=user_to_invite,
            created_by=self.user,
            cluster=self.cluster,
            duration=timedelta(days=10),
        )

        url = reverse(
            "cluster_api_v1:list_create_cluster_invitation", args=[str(self.cluster.id)]
        )

        expected_data = {
            "status": "Success",
            "code": 200,
            "count": 1,
            "next": None,
            "previous": None,
            "data": [
                {
                    "id": str(invitation_record.id),
                    "cluster": str(self.cluster.id),
                    "status": 0,
                    "duration": 10,
                    "created_by": str(self.user.id),
                    "user": str(user_to_invite.id),
                }
            ],
        }

        response = self.client.get(path=url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_list_cluster_invitation__case_2(self):
        """Test list cluster invitation when user does not have cluster view permission."""

        user_to_invite = UserModelFactory.create(email="maskon@test.com")
        ClusterInvitationFactory.create(
            user=user_to_invite,
            created_by=self.user,
            cluster=self.cluster,
            duration=timedelta(days=10),
        )

        url = reverse(
            "cluster_api_v1:list_create_cluster_invitation", args=[str(self.cluster.id)]
        )

        # remove user's view permission
        unassign_object_permissions(
            permissions=[VIEW_CLUSTER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

        response = self.client.get(path=url)

        expected_data = {
            "status": "Error",
            "code": 403,
            "data": {"detail": "You do not have permission to perform this action."},
        }

        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.json(), expected_data)

    def test_create_cluster_invitation__case_1(self):
        """Test create cluster invitation when user has add cluster member permission."""

        user_to_invite = UserModelFactory.create(email="maskon@test.com")

        url = reverse(
            "cluster_api_v1:list_create_cluster_invitation", args=[str(self.cluster.id)]
        )

        request_data = {"status": 0, "duration": 5, "user": str(user_to_invite.id)}

        with patch(
            "uia_backend.notification.tasks.send_in_app_notification_task.delay"
        ) as mock_send_in_app_notification:
            response = self.client.post(path=url, data=request_data)

        invitation_record = ClusterInvitation.objects.first()

        self.assertIsNotNone(invitation_record)

        expected_data = {
            "status": "Success",
            "code": 201,
            "data": {
                "id": str(invitation_record.id),
                "cluster": str(self.cluster.id),
                "status": 0,
                "duration": 5,
                "created_by": str(self.user.id),
                "user": str(user_to_invite.id),
            },
        }

        self.assertEqual(response.status_code, 201)
        self.assertDictEqual(response.json(), expected_data)

        self.assertEqual(invitation_record.user, user_to_invite)
        self.assertEqual(invitation_record.created_by, self.user)
        self.assertEqual(invitation_record.cluster, self.cluster)

        mock_send_in_app_notification.assert_called_once_with(
            recipients=[invitation_record.user.id],
            verb="invited you to a cluster",
            actor_dict={
                "id": str(invitation_record.created_by.id),
                "app_label": "accounts",
                "model_name": "customuser",
            },
            target_dict={
                "id": str(invitation_record.cluster.id),
                "app_label": "cluster",
                "model_name": "cluster",
            },
            notification_type=notification_constants.NOTIFICATION_TYPE_CANCELED_CLUSTER_INVITATION,
            data=dict(
                ClusterInvitationSerializer().to_representation(
                    instance=invitation_record
                )
            ),
        )

    def test_create_cluster_invitation__case_2(self):
        """Test create cluster invitation when user does not have add cluster memeber permission."""

        user_to_invite = UserModelFactory.create(email="maskon@test.com")

        url = reverse(
            "cluster_api_v1:list_create_cluster_invitation", args=[str(self.cluster.id)]
        )

        # remove user's view permission
        unassign_object_permissions(
            permissions=[ADD_CLUSTER_MEMBER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

        request_data = {"status": 0, "duration": 5, "user": str(user_to_invite.id)}
        response = self.client.post(path=url, data=request_data)

        expected_data = {
            "status": "Error",
            "code": 403,
            "data": {"detail": "You do not have permission to perform this action."},
        }

        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.json(), expected_data)
        self.assertFalse(ClusterInvitation.objects.first())

    def test_create_cluster_invitation__case_3(self):
        """Test create cluster invitation to self."""

        url = reverse(
            "cluster_api_v1:list_create_cluster_invitation", args=[str(self.cluster.id)]
        )

        request_data = {"status": 0, "duration": 5, "user": str(self.user.id)}

        response = self.client.post(path=url, data=request_data)

        expected_response = {
            "status": "Error",
            "code": 400,
            "data": {"user": ["Invalid user. Can not send inivitation to this user."]},
        }

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json(), expected_response)


class ClusterInvitationDetailAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com", is_active=True)
        self.client.force_authenticate(user=self.user)
        self.cluster = ClusterFactory.create(title="A cluster I joined")
        self.membership = ClusterMembershipFactory.create(
            cluster=self.cluster, user=self.user
        )
        assign_object_permissions(
            permissions=[
                VIEW_CLUSTER_PERMISSION,
                ADD_CLUSTER_MEMBER_PERMISSION,
                REMOVE_CLUSTER_MEMBER_PERMISSION,
            ],
            assignee=self.user,
            obj=self.cluster,
        )

    def test_retrieve_cluster_invitation__case_1(self):
        """Test retrieve cluster invitation when user has cluster view permission."""

        user_to_invite = UserModelFactory.create(email="maskon@test.com")
        invitation_record = ClusterInvitationFactory.create(
            user=user_to_invite,
            created_by=self.user,
            cluster=self.cluster,
            duration=timedelta(days=10),
        )

        url = reverse(
            "cluster_api_v1:retrieve_update_cluster_invitation",
            args=[str(self.cluster.id), str(invitation_record.id)],
        )

        expected_data = {
            "status": "Success",
            "code": 200,
            "data": {
                "id": str(invitation_record.id),
                "cluster": str(self.cluster.id),
                "status": 0,
                "duration": 10,
                "created_by": str(self.user.id),
                "user": str(user_to_invite.id),
            },
        }

        response = self.client.get(path=url)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)

    def test_retrieve_cluster_invitation__case_2(self):
        """Test retrieve cluster invitation when user does not have cluster view permission."""

        user_to_invite = UserModelFactory.create(email="maskon@test.com")
        invitation_record = ClusterInvitationFactory.create(
            user=user_to_invite,
            created_by=self.user,
            cluster=self.cluster,
            duration=timedelta(days=10),
        )

        url = reverse(
            "cluster_api_v1:retrieve_update_cluster_invitation",
            args=[str(self.cluster.id), str(invitation_record.id)],
        )

        # remove user's view permission
        unassign_object_permissions(
            permissions=[VIEW_CLUSTER_PERMISSION],
            assignee=self.user,
            obj=self.cluster,
        )

        response = self.client.get(path=url)

        expected_data = {
            "status": "Error",
            "code": 403,
            "data": {"detail": "You do not have permission to perform this action."},
        }

        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.json(), expected_data)

    def test_retrieve_cluster_invitation__case_3(self):
        """Test retrieve non-existent cluster invitation."""

        url = reverse(
            "cluster_api_v1:retrieve_update_cluster_invitation",
            args=[str(self.cluster.id), str(uuid.uuid4())],
        )

        expected_data = {
            "status": "Error",
            "code": 404,
            "data": {"detail": "Not found."},
        }

        response = self.client.get(path=url)
        self.assertEqual(response.status_code, 404)

        self.assertDictEqual(response.json(), expected_data)

    def test_update_cluster_invitation__case_1(self):
        """Test update cluster invitation when user has cluster add member permission."""

        user_to_invite = UserModelFactory.create(email="maskon@test.com")
        invitation_record = ClusterInvitationFactory.create(
            user=user_to_invite,
            created_by=self.user,
            cluster=self.cluster,
            duration=timedelta(days=10),
        )

        url = reverse(
            "cluster_api_v1:retrieve_update_cluster_invitation",
            args=[str(self.cluster.id), str(invitation_record.id)],
        )

        request_data = {"status": ClusterInvitation.INVITATION_STATUS_CANCLED}

        expected_data = {
            "status": "Success",
            "code": 200,
            "data": {
                "id": str(invitation_record.id),
                "cluster": str(self.cluster.id),
                "status": ClusterInvitation.INVITATION_STATUS_CANCLED,
                "duration": 10,
                "created_by": str(self.user.id),
                "user": str(user_to_invite.id),
            },
        }
        with patch(
            "uia_backend.notification.tasks.send_in_app_notification_task.delay"
        ) as mock_send_in_app_notification:
            response = self.client.patch(path=url, data=request_data)
            
        mock_send_in_app_notification.assert_called_once_with(
            recipients=[invitation_record.user.id],
            verb="Cancelled your invitation to cluster",
            actor_dict={
                "id": str(invitation_record.created_by.id),
                "app_label": "accounts",
                "model_name": "customuser",
            },
            target_dict={
                "id": str(invitation_record.cluster.id),
                "app_label": "cluster",
                "model_name": "cluster",
            },
            notification_type=notification_constants.NOTIFICATION_TYPE_CANCELED_CLUSTER_INVITATION,
            data=None
        )      
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)

        invitation_record.refresh_from_db()
        self.assertEqual(
            invitation_record.status, ClusterInvitation.INVITATION_STATUS_CANCLED
        )

    def test_update_cluster_invitation__case_2(self):
        """Test to show that invitation.user can not be updated."""

        user_to_invite = UserModelFactory.create(email="maskon@test.com")
        invitation_record = ClusterInvitationFactory.create(
            user=user_to_invite,
            created_by=self.user,
            cluster=self.cluster,
            duration=timedelta(days=10),
        )

        another_user = UserModelFactory.create(email="stanger@test.com")

        url = reverse(
            "cluster_api_v1:retrieve_update_cluster_invitation",
            args=[str(self.cluster.id), str(invitation_record.id)],
        )

        request_data = {"user": str(another_user.id)}

        expected_data = {
            "status": "Success",
            "code": 200,
            "data": {
                "id": str(invitation_record.id),
                "cluster": str(self.cluster.id),
                "status": 0,
                "duration": 10,
                "created_by": str(self.user.id),
                "user": str(user_to_invite.id),
            },
        }
        
        with patch(
            "uia_backend.notification.tasks.send_in_app_notification_task.delay"
        ) :
            response = self.client.patch(path=url, data=request_data)
            

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)

        invitation_record.refresh_from_db()
        self.assertEqual(invitation_record.status, 0)
        self.assertEqual(invitation_record.user, user_to_invite)


class UserClusterInvitationListAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com", is_active=True)
        self.client.force_authenticate(user=self.user)
        self.cluster = ClusterFactory.create(title="A cluster I joined")
        self.url = reverse("cluster_api_v1:list_users_cluster_invitation")

    def test_list_user_cluster_invitations(self):
        """Test list cluster invitation."""

        invitation = ClusterInvitationFactory.create(
            user=self.user,
            created_by=self.user,
            cluster=self.cluster,
            duration=timedelta(days=10),
        )
        expected_data = {
            "status": "Success",
            "code": 200,
            "count": 1,
            "next": None,
            "previous": None,
            "data": [
                {
                    "id": str(invitation.id),
                    "cluster": str(self.cluster.id),
                    "status": 0,
                    "duration": 10,
                    "created_by": str(self.user.id),
                    "user": str(self.user.id),
                }
            ],
        }
        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)


class UserClusterInvitationDetailAPIView(APITestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create(email="user@example.com", is_active=True)
        self.client.force_authenticate(user=self.user)
        self.cluster = ClusterFactory.create(title="A cluster I joined")
        self.invitation_record = ClusterInvitationFactory.create(
            user=self.user,
            created_by=self.user,
            cluster=self.cluster,
            duration=timedelta(days=10),
        )
        self.url = reverse(
            "cluster_api_v1:retrieve_update_user_cluster_invitation",
            args=[str(self.invitation_record.id)],
        )

    def test_retrieve_user_cluster_invitation__case_1(self):
        """Test retrieve user cluster invitation successfully."""

        expected_data = {
            "status": "Success",
            "code": 200,
            "data": {
                "id": str(self.invitation_record.id),
                "cluster": str(self.cluster.id),
                "status": 0,
                "duration": 10,
                "created_by": str(self.user.id),
                "user": str(self.user.id),
            },
        }

        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)

    def test_retrieve_user_cluster_invitation__case_2(self):
        """Test retrieve user cluster invitation not found."""
        url = reverse(
            "cluster_api_v1:retrieve_update_user_cluster_invitation",
            args=[str(uuid.uuid4())],
        )

        expected_data = {
            "status": "Error",
            "code": 404,
            "data": {"detail": "Not found."},
        }

        response = self.client.get(path=url)
        self.assertEqual(response.status_code, 404)

        self.assertDictEqual(response.json(), expected_data)

    def test_update_user_cluster_invitation__case_1(self):
        """Test update invitation from pending-accepted."""

        request_data = {"status": ClusterInvitation.INVITATION_STATUS_ACCEPTED}

        expected_data = {
            "status": "Success",
            "code": 200,
            "data": {
                "id": str(self.invitation_record.id),
                "cluster": str(self.cluster.id),
                "status": ClusterInvitation.INVITATION_STATUS_ACCEPTED,
                "duration": 10,
                "created_by": str(self.user.id),
                "user": str(self.user.id),
            },
        }

        with patch(
            "uia_backend.notification.tasks.send_in_app_notification_task.delay"
        ) as mock_send_in_app_notification:
            response = self.client.patch(path=self.url, data=request_data)
            
        mock_send_in_app_notification.assert_called_once_with(
            recipients=[self.invitation_record.created_by.id],
            verb="Accepted invitation to cluster",
            actor_dict={
                "id": str(self.invitation_record.user.id),
                "app_label": "accounts",
                "model_name": "customuser",
            },
            target_dict={
                "id": str(self.invitation_record.cluster.id),
                "app_label": "cluster",
                "model_name": "cluster",
            },
            notification_type=notification_constants.NOTIFICATION_TYPE_ACCEPT_CLUSTER_INVITATION,
            data=None
        )

        
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)

        self.invitation_record.refresh_from_db()
        self.assertEqual(
            self.invitation_record.status, ClusterInvitation.INVITATION_STATUS_ACCEPTED
        )

    def test_update_user_cluster_invitation__case_2(self):
        """Test update invitation from pending-rejected."""

        request_data = {"status": ClusterInvitation.INVITATION_STATUS_REJECTED}

        expected_data = {
            "status": "Success",
            "code": 200,
            "data": {
                "id": str(self.invitation_record.id),
                "cluster": str(self.cluster.id),
                "status": ClusterInvitation.INVITATION_STATUS_REJECTED,
                "duration": 10,
                "created_by": str(self.user.id),
                "user": str(self.user.id),
            },
        }
        
        with patch(
            "uia_backend.notification.tasks.send_in_app_notification_task.delay"
        ) as mock_send_in_app_notification:
            response = self.client.patch(path=self.url, data=request_data)
             
        mock_send_in_app_notification.assert_called_once_with(
            recipients=[self.invitation_record.created_by.id],
            verb="rejected invitation to cluster",
            actor_dict={
                "id": str(self.invitation_record.user.id),
                "app_label": "accounts",
                "model_name": "customuser",
            },
            target_dict={
                "id": str(self.invitation_record.cluster.id),
                "app_label": "cluster",
                "model_name": "cluster",
            },
            notification_type=notification_constants.NOTIFICATION_TYPE_REJECT_CLUSTER_INVITATION,
            data=None
        )

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_data)


        self.invitation_record.refresh_from_db()
        self.assertEqual(
            self.invitation_record.status, ClusterInvitation.INVITATION_STATUS_REJECTED
        )
