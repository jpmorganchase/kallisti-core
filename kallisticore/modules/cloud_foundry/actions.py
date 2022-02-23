import random

from chaoscf.actions import terminate_app_instance, \
    terminate_some_random_instance
from chaoscf.api import get_apps_for_org, get_app_instances
from chaoslib import Configuration, Secrets
from chaoslib.exceptions import FailedActivity

__all__ = ['get_app_states_by_org', 'terminate_random_app_instance',
           'terminate_some_random_instances']


def get_app_states_by_org(org_name: str, configuration: Configuration,
                          secrets: Secrets):
    apps = get_apps_for_org(org_name, configuration, secrets)['resources']
    if not apps:
        raise FailedActivity(
            "no app was found under org: '{o}'.".format(o=org_name))
    result = []
    for app in apps:
        result.append({
            'name': app['entity']['name'],
            'state': app['entity']['state']
        })
    return result


def terminate_random_app_instance(org_name: str, configuration: Configuration,
                                  secrets: Secrets):
    """
    Terminate a random instance under a randomly picked app for a specified
    org name.
    """
    apps = get_apps_for_org(org_name, configuration, secrets)

    app_names = [app['entity']['name'] for app in apps['resources']]
    app_name = random.choice(app_names)

    terminate_some_random_instance(app_name, configuration, secrets, org_name)


def terminate_some_random_instances(app_name: str,
                                    configuration: Configuration,
                                    secrets: Secrets, count: int = 0,
                                    percentage: int = 0, org_name: str = None,
                                    space_name: str = None):
    """
    Terminate random instances under a specified app.

    The number of instances to terminate can be specified by count or
    percentage. When both of count and percentage are specified, percentage
    overrides the count. When the number of instances to terminate is bigger
    than the one of existing instances, all instances will be terminated.
    """
    instances = get_app_instances(
        app_name, configuration, secrets, org_name=org_name,
        space_name=space_name)

    indices = [idx for idx in instances.keys()]
    instance_count = len(indices)

    if percentage > 0:
        count = int(instance_count * percentage / 100)

    indices_to_terminate = random.sample(indices, min(count, instance_count))

    for idx in indices_to_terminate:
        terminate_app_instance(
            app_name, idx, configuration, secrets, org_name, space_name)
