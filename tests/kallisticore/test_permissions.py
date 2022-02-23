from unittest import mock

import kallisticore.authentication
import kallisticore.permissions
from django.test import TestCase


class TestDefaultPermission(TestCase):

    def test_has_permission(self):
        permission = kallisticore.permissions.DefaultUserPermission()
        request_mock = mock.Mock()
        request_mock.method = 'GET'
        request_mock.META = {'HTTP_AUTHORIZATION': "bearer my-access-token"}
        view_mock = mock.Mock()

        self.assertTrue(permission.has_permission(request_mock, view_mock))
