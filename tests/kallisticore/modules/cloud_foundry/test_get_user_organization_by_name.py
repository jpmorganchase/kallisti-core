from unittest import TestCase, mock

import kallisticore.modules.cloud_foundry
from chaoslib.exceptions import FailedActivity
from kallisticore.modules.cloud_foundry import get_user_organization_by_name

ORG_NAME = 'MY_ORG'
ORGANIZATIONS = {
    'total_results': 1, 'total_pages': 1, 'prev_url': None,
    'next_url': None, 'resources': [{
        'metadata': {
            'guid': 'org-guid-1',
            'url': '/v2/organizations/org-guid-1',
            'created_at': '2017-07-31T08:56:45Z',
            'updated_at': '2017-07-31T08:56:45Z'},
        'entity': {
            'name': ORG_NAME,
            'spaces_url': '/v2/organizations/org-guid-1/spaces',
            'users_url': '/v2/organizations/org-guid-1/users', }}]}


class TestGetUserOrganizationByName(TestCase):
    def setUp(self):
        self.user_guid = 'user-uid-1'
        self.configuration = {}
        self.secrets = {'cf_access_token': 'secret-token',
                        'cf_token_type': 'bearer'}
        self.mock_response = mock.Mock()
        self.mock_response.json.return_value = ORGANIZATIONS
        self.patch_call_api = mock.patch.object(
            kallisticore.modules.cloud_foundry, 'call_api',
            return_value=self.mock_response)
        self.patch_call_api.start()

    def tearDown(self):
        self.patch_call_api.stop()

    def test_get_a_organization_by_name_for_user(self):
        result = get_user_organization_by_name(
            user_guid=self.user_guid, org_name=ORG_NAME,
            configuration=self.configuration, secrets=self.secrets)
        self.assertEqual(ORGANIZATIONS['resources'][0], result)
        self.patch_call_api.target.call_api.assert_called_once_with(
            '/v2/users/{}/organizations'
            '?q=name:{}'.format(self.user_guid, ORG_NAME),
            method='GET',
            configuration=self.configuration,
            secrets=self.secrets)

    def test_function_should_raise_a_failed_activity_exception(self):
        self.mock_response.json.return_value = {
            'total_results': 0,
            'total_pages': 1,
            'prev_url': None,
            'next_url': None,
            'resources': []
        }
        with self.assertRaises(FailedActivity) as error:
            get_user_organization_by_name(user_guid=self.user_guid,
                                          org_name=ORG_NAME,
                                          configuration=self.configuration,
                                          secrets=self.secrets)
        self.assertEqual('org \'MY_ORG\' was not found',
                         str(error.exception))
