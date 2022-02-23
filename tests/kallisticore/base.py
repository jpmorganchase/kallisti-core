from unittest import mock

import kallisticore.authentication
import kallisticore.permissions
from kallisticore.authentication import KallistiUser
from rest_framework.test import APITestCase


class KallistiTestSuite(APITestCase):

    def setUp(self):
        self.permission_patch = mock.patch.object(
            kallisticore.permissions.DefaultUserPermission, "has_permission",
            return_value=True)
        self.addCleanup(self.permission_patch.stop)
        self.permission_patch.start()

        self.authentication_patch = mock.patch.object(
            kallisticore.authentication.DefaultAuthentication, "authenticate",
            return_value=(KallistiUser(user_id='A123123'), None))
        self.addCleanup(self.authentication_patch.stop)
        self.authentication_patch.start()
