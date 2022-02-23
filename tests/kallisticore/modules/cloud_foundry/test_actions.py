from unittest import TestCase, mock

from chaoslib.exceptions import FailedActivity
from kallisticore.modules.cloud_foundry.actions import get_app_states_by_org, \
    terminate_random_app_instance, \
    terminate_some_random_instances


class TestActions(TestCase):
    response_stub_app_1 = {
        'entity': {
            'name': 'test-name-1',
            'state': 'test-state-a'
        }
    }
    response_stub_app_2 = {
        'entity': {
            'name': 'test-name-2',
            'state': 'test-state-b'
        }
    }
    response_stub_apps = {
        'resources': [response_stub_app_1, response_stub_app_2]
    }
    response_stub_instance_1 = {
        'state': 'RUNNING',
        'uptime': 999,
        'since': 1515413624
    }
    response_stub_instance_2 = {
        'state': 'RUNNING',
        'uptime': 999,
        'since': 1515413624
    }
    response_stub_instances = {
        '0': response_stub_instance_1,
        '1': response_stub_instance_2
    }
    mock_config = {}
    mock_secret = {}

    @mock.patch('kallisticore.modules.cloud_foundry.actions.get_apps_for_org')
    def test_get_app_states_success(self, mock_get_apps_for_org):
        mock_get_apps_for_org.return_value = self.response_stub_apps
        expected = [
            {
                'name': 'test-name-1',
                'state': 'test-state-a'
            },
            {
                'name': 'test-name-2',
                'state': 'test-state-b'
            }
        ]
        result = get_app_states_by_org('test-org', self.mock_config,
                                       self.mock_secret)
        self.assertEqual(2, len(result))
        self.assertEqual(expected, result)

    @mock.patch('kallisticore.modules.cloud_foundry.actions.get_apps_for_org')
    def test_get_app_states_by_org_empty_response(self, mock_get_apps_for_org):
        mock_get_apps_for_org.return_value = {
            'resources': []
        }
        with self.assertRaises(FailedActivity) as err_context:
            get_app_states_by_org('test-org', self.mock_config,
                                  self.mock_secret)
            expected_err_message = "no app was found under org: 'test-org'."
            self.assertEqual(str(err_context.exception), expected_err_message)

    @mock.patch('kallisticore.modules.cloud_foundry.actions.random')
    @mock.patch('kallisticore.modules.cloud_foundry.actions.'
                'terminate_some_random_instance')
    @mock.patch('kallisticore.modules.cloud_foundry.actions.get_apps_for_org')
    def test_terminate_random_app_instance(self, mock_get_apps_for_org,
                                           mock_terminate_random_instance,
                                           mock_random):
        mock_get_apps_for_org.return_value = self.response_stub_apps
        mock_random.choice.return_value = self.response_stub_app_1['entity'][
            'name']

        terminate_random_app_instance('test-org', self.mock_config,
                                      self.mock_secret)

        expected_app_names = [self.response_stub_app_1['entity']['name'],
                              self.response_stub_app_2['entity']['name']]
        mock_random.choice.assert_called_once_with(expected_app_names)

        mock_terminate_random_instance.assert_called_once_with(
            self.response_stub_app_1['entity']['name'],
            self.mock_config, self.mock_secret, 'test-org')

    @mock.patch('kallisticore.modules.cloud_foundry.actions.random')
    @mock.patch('kallisticore.modules.cloud_foundry.actions.'
                'terminate_app_instance')
    @mock.patch('kallisticore.modules.cloud_foundry.actions.get_app_instances')
    def test_terminate_some_random_instances_with_count(
            self, mock_get_app_instances, mock_terminate_app_instance,
            mock_random):
        mock_get_app_instances.return_value = self.response_stub_instances
        mock_random.sample.return_value = ['0']
        terminate_some_random_instances('test-app', self.mock_config,
                                        self.mock_secret, count=1)

        expected_indices = ['0', '1']
        mock_random.sample.assert_called_once_with(expected_indices, 1)

        mock_terminate_app_instance.assert_called_once_with(
            'test-app', '0', self.mock_config, self.mock_secret, None, None)

    @mock.patch('kallisticore.modules.cloud_foundry.actions.random')
    @mock.patch('kallisticore.modules.cloud_foundry.actions.'
                'terminate_app_instance')
    @mock.patch('kallisticore.modules.cloud_foundry.actions.get_app_instances')
    def test_terminate_some_random_instances_with_percentage(
            self, mock_get_app_instances, mock_terminate_app_instance,
            mock_random):
        mock_get_app_instances.return_value = self.response_stub_instances
        mock_random.sample.return_value = ['0']
        terminate_some_random_instances('test-app', self.mock_config,
                                        self.mock_secret, percentage=100)

        expected_indices = ['0', '1']
        mock_random.sample.assert_called_once_with(expected_indices, 2)

        mock_terminate_app_instance.assert_called_once_with(
            'test-app', '0', self.mock_config, self.mock_secret, None, None)
