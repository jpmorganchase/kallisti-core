from huey import crontab

from kallisticore.lib import trial_executor
from django.conf import settings

from kallisticore.lib.trial_scheduler import schedule


@settings.HUEY.task()
def execute_trial(instance):
    _execute_trial(instance)


def _execute_trial(instance):
    action_module_map = getattr(settings, 'KALLISTI_MODULE_MAP', {})
    cred_class_map = getattr(settings, 'KALLISTI_CREDENTIAL_CLASS_MAP', {})
    with trial_executor.TrialExecutor(
            instance, action_module_map, cred_class_map) as executor:
        for observer in getattr(settings, 'KALLISTI_TRIAL_OBSERVERS', []):
            executor.attach(observer())
        executor.run()


@settings.HUEY.periodic_task(crontab())
def schedule_trials():
    _schedule_trials(60)


def _schedule_trials(scheduler_interval_seconds):
    schedule(scheduler_interval_seconds)
