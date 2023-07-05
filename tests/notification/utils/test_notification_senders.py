from django.test import TestCase

from tests.accounts.test_models import UserModelFactory
from uia_backend.notification.models import NotificationModel
from uia_backend.notification.utils.notification_senders import send_in_app_notifcation


class SendInAppNotifcationTests(TestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()

    def test_method(self):
        send_in_app_notifcation(
            recipient=self.user,
            sender=self.user,
            verb="John doe Just Joined the team.",
            type="",
            metadata=None,
        )

        self.assertTrue(
            NotificationModel.objects.filter(
                recipient=self.user,
                actor_object_id=self.user.id,
                verb="John doe Just Joined the team.",
                type="",
                data={},
            ).exists()
        )
