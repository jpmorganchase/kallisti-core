from django.conf import settings
from huey import crontab

from kallisticore.lib.trial_executor import execute_trial as exec_trial
from kallisticore.lib.trial_scheduler import schedule


@settings.HUEY.task()
def execute_trial(instance):
    exec_trial(instance)


@settings.HUEY.periodic_task(crontab())
def schedule_trials():
    _schedule_trials(60)


def _schedule_trials(scheduler_interval_seconds):
    schedule(scheduler_interval_seconds)
