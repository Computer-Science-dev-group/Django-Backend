import uuid

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import serializers
from rest_framework.test import APITestCase

from tests.accounts.test_models import UserModelFactory
from tests.notification.test_models import NotificationModelFactory
from uia_backend.accounts.api.v1.serializers import ProfileSerializer


class NotificationListAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.authenticated_user = UserModelFactory.create(email="user_1@example.com")
        self.user = UserModelFactory.create(email="user_2@example.com")
        self.url = reverse("notification_api_v1:user_notifications")

    def test_list_userntifications_successfully(self):
        self.client.force_authenticate(user=self.authenticated_user)

        # authenticated users notification
        notification_record = NotificationModelFactory.create(
            recipient=self.authenticated_user,
            actor_content_type=ContentType.objects.get_for_model(
                self.user,
                for_concrete_model=True,
            ),
            actor_object_id=self.user.id,
            target_content_type=ContentType.objects.get_for_model(
                self.user,
                for_concrete_model=True,
            ),
            target_object_id=self.user.id,
            verb="Some cool action",
            type="",
            data={"msg": "Well hello there"},
        )

        # another users notification (will not be added to response)
        NotificationModelFactory.create(
            recipient=self.user,
            actor_content_type=ContentType.objects.get_for_model(
                self.user,
                for_concrete_model=True,
            ),
            actor_object_id=self.user.id,
            target_content_type=ContentType.objects.get_for_model(
                self.user,
                for_concrete_model=True,
            ),
            target_object_id=self.user.id,
            verb="Some cool action",
            type="",
            data={"msg": "Well hello there"},
        )

        user_profile_data = dict(
            ProfileSerializer().to_representation(instance=self.user)
        )

        response = self.client.get(path=self.url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "count": 1,
                "next": None,
                "previous": None,
                "data": [
                    {
                        "id": str(notification_record.id),
                        "type": "",
                        "verb": "Some cool action",
                        "timestamp": serializers.DateTimeField().to_representation(
                            notification_record.timestamp
                        ),
                        "actor": user_profile_data,
                        "target": user_profile_data,
                        "unread": True,
                        "data": {"msg": "Well hello there"},
                    },
                ],
            },
        )

    def test_fails__unauthroized(self):
        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )


class NotificationDetailAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.authenticated_user = UserModelFactory.create(email="user_1@example.com")
        self.user = UserModelFactory.create(email="user_2@example.com")
        self.notification_record = NotificationModelFactory.create(
            recipient=self.authenticated_user,
            actor_content_type=ContentType.objects.get_for_model(
                self.user,
                for_concrete_model=True,
            ),
            actor_object_id=self.user.id,
            target_content_type=ContentType.objects.get_for_model(
                self.user,
                for_concrete_model=True,
            ),
            target_object_id=self.user.id,
            verb="Some cool action",
            type="",
            data={"msg": "Well hello there"},
        )
        self.maxDiff = None
        self.user_profile_data = dict(
            ProfileSerializer().to_representation(instance=self.user)
        )
        self.url = reverse(
            "notification_api_v1:notification_details",
            args=[str(self.notification_record.id)],
        )

    def test_fails__unauthroized(self):
        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )

    def test_retrieve_record_successfully(self):
        self.client.force_authenticate(self.authenticated_user)

        response = self.client.get(path=self.url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.notification_record.id),
                    "type": "",
                    "verb": "Some cool action",
                    "timestamp": serializers.DateTimeField().to_representation(
                        self.notification_record.timestamp
                    ),
                    "actor": self.user_profile_data,
                    "target": self.user_profile_data,
                    "unread": True,
                    "data": {"msg": "Well hello there"},
                },
            },
        )

    def test_retrieve_record__not_found(self):
        self.client.force_authenticate(self.authenticated_user)

        url = reverse(
            "notification_api_v1:notification_details", args=[str(uuid.uuid4())]
        )
        response = self.client.get(path=url)
        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            response.json(),
            {"status": "Error", "code": 404, "data": {"detail": "Not found."}},
        )

        # Test to ensure that not found is returned if non-recipient tries to access the record
        self.client.force_authenticate(self.user)
        response = self.client.get(path=self.url)
        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            response.json(),
            {"status": "Error", "code": 404, "data": {"detail": "Not found."}},
        )

    def test_update_record_successfully(self):
        self.client.force_authenticate(self.authenticated_user)

        data = {"unread": False}

        response = self.client.patch(path=self.url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "Success",
                "code": 200,
                "data": {
                    "id": str(self.notification_record.id),
                    "type": "",
                    "verb": "Some cool action",
                    "timestamp": serializers.DateTimeField().to_representation(
                        self.notification_record.timestamp
                    ),
                    "actor": self.user_profile_data,
                    "target": self.user_profile_data,
                    "unread": False,
                    "data": {"msg": "Well hello there"},
                },
            },
        )

        self.notification_record.refresh_from_db()
        self.assertFalse(self.notification_record.unread)


class MarkAllNotifcationsAsReadAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.authenticated_user = UserModelFactory.create(email="user_1@example.com")
        self.user = UserModelFactory.create(email="user_2@example.com")
        self.notification_records = NotificationModelFactory.create_batch(
            size=3,
            recipient=self.authenticated_user,
            actor_content_type=ContentType.objects.get_for_model(
                self.user,
                for_concrete_model=True,
            ),
            actor_object_id=self.user.id,
            target_content_type=ContentType.objects.get_for_model(
                self.user,
                for_concrete_model=True,
            ),
            target_object_id=self.user.id,
            verb="Some cool action",
            type="",
            data={"msg": "Well hello there"},
        )

        self.url = reverse("notification_api_v1:read_all_notification")

    def test_mark_all_notifications_as_read_successfully(self):
        self.client.force_authenticate(self.authenticated_user)

        response = self.client.post(path=self.url, data={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"status": "Success", "code": 200, "data": {}}
        )

        for notification in self.notification_records:
            notification.refresh_from_db()
            self.assertFalse(notification.unread)

    def test_mark_all_notifications_as_read_only_marks_user_notifications(self):
        user_notification_record = NotificationModelFactory.create(
            recipient=self.user,
            actor_content_type=ContentType.objects.get_for_model(
                self.user,
                for_concrete_model=True,
            ),
            actor_object_id=self.user.id,
            target_content_type=ContentType.objects.get_for_model(
                self.user,
                for_concrete_model=True,
            ),
            target_object_id=self.user.id,
            verb="Some cool action",
            type="",
            data={"msg": "Well hello there"},
        )

        self.client.force_authenticate(self.user)

        response = self.client.post(path=self.url, data={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"status": "Success", "code": 200, "data": {}}
        )

        user_notification_record.refresh_from_db()
        self.assertFalse(user_notification_record.unread)

        for notification in self.notification_records:
            notification.refresh_from_db()
            self.assertTrue(notification.unread)

    def test_fails__unauthroized(self):
        response = self.client.get(path=self.url)

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            response.json(),
            {
                "status": "Error",
                "code": 401,
                "data": {"detail": "Authentication credentials were not provided."},
            },
        )
