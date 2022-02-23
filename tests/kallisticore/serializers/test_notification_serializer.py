from django.test import TestCase

from kallisticore.models.notification import Notification
from kallisticore.serializers import NotificationSerializer


def update_notification_list():
    notification = Notification.objects.get(pk=1)
    notification.emails = ['sample@test.com']
    notification.save()


class TestNotificationSerializer(TestCase):

    def test_notification_fetch(self):
        update_notification_list()
        notification = Notification.objects.get(pk=1)
        serializer = NotificationSerializer(notification)
        notification_data = serializer.data

        self.assertEqual(notification_data['emails'], ['sample@test.com'])
