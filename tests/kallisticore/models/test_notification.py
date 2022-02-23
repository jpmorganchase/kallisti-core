from django.test import TestCase

from kallisticore.models.notification import Notification


def update_notification_list():
    notification = Notification.objects.get(pk=1)
    notification.emails = ['sample@test.com']
    notification.save()


class TestNotification(TestCase):

    def test_notification_fetch_for_empty_list(self):
        notifications = Notification.objects.all()
        notification = notifications[0]
        self.assertEqual(notification.emails, [])

    def test_notification_fetch_for_list(self):
        update_notification_list()
        notifications = Notification.objects.all()
        notification = notifications[0]
        self.assertEqual(notification.emails, ['sample@test.com'])

    def test_notification_delete(self):
        update_notification_list()
        self.assertNotEqual(len(Notification.objects.all()), 0)
        Notification.delete()
        self.assertEqual(len(Notification.objects.all()), 0)
