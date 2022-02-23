import os
import unittest
from unittest.mock import patch

from kallisticore.exceptions import InvalidCredentialType
from kallisticore.lib.credential import Credential, \
    EnvironmentUserNamePasswordCredential


class TestCredential(unittest.TestCase):
    CRED_CLS_MAP = {
        'ENV_VAR_USERNAME_PASSWORD': 'kallisticore.lib.credential.'
                                     'EnvironmentUserNamePasswordCredential'}

    def test_build_throws_an_error_when_dict_type_not_present(self):
        credential_dict = {}

        with self.assertRaises(InvalidCredentialType) as error:
            Credential.build({}, credential_dict)

        self.assertEqual("Invalid credential type: None",
                         error.exception.message)

    def test_build_throws_an_error_when_dict_type_is_invalid(self):
        credential_dict = {'type': 'INVALID_CRED'}

        with self.assertRaises(InvalidCredentialType) as error:
            Credential.build({}, credential_dict)

        self.assertEqual("Invalid credential type: INVALID_CRED",
                         error.exception.message)

    def test_build_env_var_username_password(self):
        username_key = "USERNAME"
        password_key = "PASSWORD"
        credential_dict = {"type": "ENV_VAR_USERNAME_PASSWORD",
                           "username_key": username_key,
                           "password_key": password_key}

        cred = Credential.build(self.CRED_CLS_MAP, credential_dict)

        self.assertIsInstance(cred, Credential)
        self.assertIsInstance(cred, EnvironmentUserNamePasswordCredential)
        self.assertEqual(username_key, cred.username_key)
        self.assertEqual(password_key, cred.password_key)

    @patch.multiple(Credential, __abstractmethods__=set())
    def test_fetch(self):
        with self.assertRaises(NotImplementedError):
            Credential().fetch()


class TestEnvironmentUserNamePasswordCredential(unittest.TestCase):
    user_name = 'A111111'
    user_pword = 'some-secure-pass'

    def setUp(self):
        self.username_key = "ENV_VAR_USERNAME"
        self.password_key = "ENV_VAR_PASSWORD"

        self.username = TestEnvironmentUserNamePasswordCredential.user_name
        self.password = TestEnvironmentUserNamePasswordCredential.user_pword
        os.environ[self.username_key] = self.username
        os.environ[self.password_key] = self.password

        self.credentials = EnvironmentUserNamePasswordCredential(
            username_key=self.username_key,
            password_key=self.password_key)

    def tearDown(self):
        os.environ.pop(self.username_key)
        os.environ.pop(self.password_key)

    def test_initialize(self):
        self.assertEqual(self.username_key, self.credentials.username_key)
        self.assertEqual(self.password_key, self.credentials.password_key)

    def test_fetch(self):
        self.credentials.fetch()

        self.assertEqual(self.username, self.credentials.username)
        self.assertEqual(self.password, self.credentials.password)
