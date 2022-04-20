from django.urls import reverse
from rest_framework import status

from kallisticore.models.notification import Notification
from tests.kallisticore.base import KallistiTestSuite


def update_notification_list():
    notification = Notification.objects.get(pk=1)
    notification.emails = ['sample@test.com']
    notification.save()


class TestNotificationListAPI(KallistiTestSuite):

    def setUp(self):
        super(TestNotificationListAPI, self).setUp()
        self._token = '123123123123123'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)

    def tearDown(self):
        self.client.credentials()
        super(TestNotificationListAPI, self).tearDown()

    def test_list_empty(self):
        url = reverse('notification')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'emails': []})

    def test_list(self):
        update_notification_list()
        url = reverse('notification')
        response = self.client.get(url, format='json')

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'emails': ['sample@test.com']})


class TestNotificationPutAPI(KallistiTestSuite):
    def setUp(self):
        super(TestNotificationPutAPI, self).setUp()
        self._data = {'emails': ['123@email.com']}
        self._token = '123123123123123'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)

    def tearDown(self):
        self.client.credentials()
        super(TestNotificationPutAPI, self).tearDown()

    def test_put(self):
        update_notification_list()

        url = reverse('notification', args=[])
        response = self.client.put(url, data=self._data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.count(), 1)
