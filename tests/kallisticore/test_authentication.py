from unittest import TestCase
from unittest import mock
from unittest.mock import Mock

from django.test import override_settings
from kallisticore.authentication import KallistiUser, DefaultAuthentication
from rest_framework import exceptions


class TestCFAuthentication(TestCase):
    @override_settings(KALLISTI_AUTH_JWT_TOKEN_URL='jwt.test')
    @override_settings(KALLISTI_AUTH_JWKS_URL='jwt.test')
    @override_settings(KALLISTI_AUTH_JWT_AUDIENCE='jwt.test')
    def test_no_token(self):
        request_mock = Mock()
        request_mock.META.get.return_value = ""
        auth = DefaultAuthentication()
        with self.assertRaises(exceptions.AuthenticationFailed) as error:
            auth.authenticate(request_mock)

        exception_details = error.exception.get_full_details()
        self.assertEqual('No authorization token found.',
                         exception_details['message'])

    @override_settings(KALLISTI_AUTH_JWT_TOKEN_URL='jwt.test')
    @override_settings(KALLISTI_AUTH_JWKS_URL='jwt.test')
    @override_settings(KALLISTI_AUTH_JWT_AUDIENCE='jwt.test')
    @mock.patch('kallisticore.authentication.JwtHandler')
    def test_authenticate(self, mock_jwt_handler_cls):
        mock_claim = {'sub': 'test-user',
                      'other-claim-key': 'other-claim-value'}
        mock_jwt_handler = mock.Mock()
        mock_jwt_handler.decode.return_value = mock_claim
        mock_jwt_handler_cls.return_value = mock_jwt_handler
        request_mock = Mock()
        request_mock.META.get.return_value = 'Bearer test-token'

        auth = DefaultAuthentication()
        user, auth_value = auth.authenticate(request_mock)

        self.assertIsInstance(user, KallistiUser)
        self.assertEqual('test-user', user.user_id)
        self.assertIsNone(user.domain)
        self.assertEqual(mock_claim, user.claims)
        self.assertIsNone(auth_value)


class TestKallistiUser(TestCase):
    def setUp(self):
        self.user_id = 'test-user-id'
        self.domain = 'test-domain'
        self.claims = {'key': 'value'}
        self.user = KallistiUser(user_id=self.user_id, domain=self.domain,
                                 claims=self.claims)

    def test_initialize(self):
        self.assertEqual(self.user_id, self.user.user_id)
        self.assertEqual(self.domain, self.user.domain)
        self.assertDictEqual(self.claims, self.user.claims)

    def test_kallisti_user_as_a_dict(self):
        self.assertEqual(self.user_id, self.user['user_id'])
        self.assertEqual(self.domain, self.user['domain'])
        self.assertDictEqual(self.claims, self.user['claims'])

    def test_set_values_like_dict(self):
        new_user_id = 'new-user-id'
        self.user['user_id'] = new_user_id

        self.assertEqual(new_user_id, self.user.user_id)

    def test_str(self):
        user_str = str(self.user)
        self.assertTrue(user_str.startswith('KallistiUser({'))
        self.assertTrue(user_str.endswith("})"))
        self.assertIn("'user_id': 'test-user-id'", user_str)
        self.assertIn("'domain': 'test-domain'", user_str)
        self.assertIn("'claims': {'key': 'value'}", user_str)

    def test_get_claim(self):
        self.assertEqual("value", self.user.get_claim("key"))

    def test_get_claim_without_claim_key(self):
        self.assertIsNone(self.user.get_claim("invalid"))
