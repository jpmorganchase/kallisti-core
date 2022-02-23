from typing import Dict, Any

from chaoscf.api import call_api, get_org_by_name
from chaoslib import Configuration, Secrets
from chaoslib.exceptions import FailedActivity

from .cloud_foundry_action import CloudFoundryAction

__action_class__ = CloudFoundryAction

__actions_modules__ = ['chaoscf.actions',
                       'chaoscf.api',
                       'chaoscf.probes',
                       'kallisticore.modules.cloud_foundry.actions']


def get_user_organization_by_name(user_guid: str, org_name: str,
                                  configuration: Configuration,
                                  secrets: Secrets) -> Dict[str, Any]:
    url = '/v2/users/{}/organizations?q=name:{}'.format(user_guid, org_name)
    response = call_api(url, configuration=configuration, secrets=secrets,
                        method='GET').json()
    if response['total_results'] == 1:
        return response['resources'][0]

    raise FailedActivity('org \'{o}\' was not found'.format(o=org_name))


def get_user_space_by_organization_and_space_name(
        user_guid: str, org_name: str, space_name: str,
        configuration: Configuration, secrets: Secrets) -> Dict[str, Any]:
    query = []

    org = get_org_by_name(org_name, configuration, secrets)
    org_guid = org['metadata']['guid']
    query.append('organization_guid:{o}'.format(o=org_guid))

    query.append('developer_guid:{n}'.format(n=user_guid))

    if space_name:
        query.append('name:{s}'.format(s=space_name))
    spaces = call_api('/v2/spaces', configuration,
                      secrets, query={'q': query}).json()

    if not spaces['total_results']:
        raise FailedActivity(
            'space \'{s}\' was not found'.format(s=space_name))

    return spaces['resources'][0]


def _get(path: str, configuration: Configuration, secrets: Secrets,
         params: Dict[str, Any] = None) -> Dict:
    return call_api(path, configuration=configuration, secrets=secrets,
                    query=params, method='GET').json()
