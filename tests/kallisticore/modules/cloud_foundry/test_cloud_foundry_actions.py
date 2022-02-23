import os
from unittest import TestCase, mock
from unittest.mock import ANY

from kallisticore.models.step import Step
from kallisticore.modules.cloud_foundry.cloud_foundry_action import \
    CloudFoundryAction
from tests import clear_kallisti_functions_cache


class TestCFAction(TestCase):
    user_name = 'user_name'
    user_pw = 'user_password'
    module_map = {'cf': 'kallisticore.modules.cloud_foundry'}
    cred_cls_map = {
        'ENV_VAR_USERNAME_PASSWORD': 'kallisticore.lib.credential.'
                                     'EnvironmentUserNamePasswordCredential'}

    def setUp(self):
        self.org_name = 'org'
        self.cf_api_url = 'https://cf-api.test'
        self.arguments = {'cf_api_url': self.cf_api_url,
                          'org_name': self.org_name}
        self.action_spec = {'step': 'get_org_by_name',
                            'do': 'cf.get_org_by_name',
                            'where': self.arguments}
        self.step = Step.build(self.action_spec)
        clear_kallisti_functions_cache()

    def test_init_cloud_foundry_action_for_local_environment(self):
        self.user_name = TestCFAction.user_name
        self.password = TestCFAction.user_pw
        os.environ[CloudFoundryAction.CF_DEFAULT_USERNAME_KEY] = \
            TestCFAction.user_name
        os.environ[
            CloudFoundryAction.CF_DEFAULT_PASSWORD_KEY] = TestCFAction.user_pw

        cf_action = CloudFoundryAction.build(self.step, self.module_map,
                                             self.cred_cls_map)

        self.assertEqual(self.org_name, cf_action.arguments['org_name'])
        self.assertDictEqual({'cf_client_id': 'cf',
                              'cf_client_secret': '',
                              'cf_username': TestCFAction.user_name,
                              'cf_password': TestCFAction.user_pw},
                             cf_action.arguments['secrets'])
        self.assertDictEqual(
            {'cf_verify_ssl': True, 'cf_api_url': self.cf_api_url},
            cf_action.arguments['configuration'])

    def test_init_cloud_foundry_action_when_credentials_are_passed(self):
        username_key = 'CRED_USERNAME'
        password_key = 'CRED_PASSWORD'
        os.environ[username_key] = TestCFAction.user_name
        os.environ[password_key] = TestCFAction.user_pw

        step = Step.build({'step': 'Get org by name',
                           'do': 'cf.get_org_by_name',
                           'where': {'cf_api_url': self.cf_api_url,
                                     'org_name': self.org_name,
                                     'credentials': {
                                         'type': 'ENV_VAR_USERNAME_PASSWORD',
                                         'username_key': username_key,
                                         'password_key': password_key}}})
        cf_action = CloudFoundryAction.build(step, self.module_map,
                                             self.cred_cls_map)

        self.assertEqual(self.org_name, cf_action.arguments['org_name'])
        self.assertDictEqual({'cf_client_id': 'cf',
                              'cf_client_secret': '',
                              'cf_username': TestCFAction.user_name,
                              'cf_password': TestCFAction.user_pw},
                             cf_action.arguments['secrets'])
        self.assertDictEqual({'cf_verify_ssl': True,
                              'cf_api_url': self.cf_api_url},
                             cf_action.arguments['configuration'])

    def test_execute_should_call_chaostoolkit_function_implementation(self):
        with mock.patch('chaoscf.api.get_org_by_name') as mock_func:
            action = CloudFoundryAction.build(self.step, self.module_map,
                                              self.cred_cls_map)
            action.execute()
        self.assertIsInstance(action, CloudFoundryAction)
        mock_func.assert_called_with(
            org_name=self.org_name, secrets=ANY,
            configuration={'cf_api_url': self.cf_api_url,
                           'cf_verify_ssl': True})
