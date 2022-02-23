from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings

from kallisticore.models import Trial
from kallisticore.tasks import execute_trial


@receiver(post_save, sender=Trial)
def execute_plan_for_trial(sender, instance, created, **kwargs):
    if created:
        execute_trial(_before_trial_task_creation(instance))


@receiver(pre_save, sender=Trial)
def execute_full_clean_for_trial(sender, instance, **kwargs):
    instance.full_clean()


def _before_trial_task_creation(trial: Trial):
    for hook in getattr(settings, 'TRIAL_TASK_CREATION_HOOKS', []):
        hook(trial)
    return trial
