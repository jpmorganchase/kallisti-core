from datetime import datetime

from kallisticore.models import Trial
from kallisticore.models.trial_schedule import TrialSchedule


def schedule(scheduler_interval_seconds):
    current_datetime = _get_current_datetime()
    for trial_schedule in TrialSchedule.objects.get_queryset().all():
        if trial_schedule.should_execute_at(current_datetime,
                                            scheduler_interval_seconds):
            trial = Trial.create(experiment=trial_schedule.experiment,
                                 parameters=trial_schedule.parameters,
                                 ticket=trial_schedule.ticket,
                                 metadata=trial_schedule.metadata)
            trial_schedule.decrement_recurrence_left()
            trial_schedule.trials.add(trial)


def _get_current_datetime() -> datetime:
    return datetime.now()
