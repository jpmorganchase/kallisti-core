from copy import deepcopy
from datetime import datetime
from uuid import uuid4

from croniter import croniter
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from kallisticore.models.base_model import BaseModel
from kallisticore.models.experiment import Experiment
from kallisticore.models.trial import validate_trial_ticket, Trial
from kallisticore.utils.fields import DictField


def validate_recurrence_pattern(pattern_value):
    if croniter.is_valid(pattern_value):
        return True
    raise ValidationError("%(value)s is not a valid cron expression",
                          params={'value': pattern_value})


class TrialScheduleManager(models.Manager):
    def get_queryset(self, **kwargs):
        return super(TrialScheduleManager, self).get_queryset().filter(
            deleted_at=None, experiment__deleted_at=None, **kwargs)

    def get_queryset_all(self, **kwargs):
        return super(TrialScheduleManager, self)\
            .get_queryset().filter(**kwargs)


class TrialSchedule(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    experiment = models.ForeignKey(Experiment, related_name='schedules',
                                   on_delete=models.DO_NOTHING)
    trials = models.ManyToManyField(Trial, related_name="trial_schedules")
    parameters = DictField(default={}, blank=True)
    metadata = DictField(default={}, blank=True)
    ticket = DictField(default={}, blank=True,
                       validators=[validate_trial_ticket])
    recurrence_pattern = models.CharField(max_length=20, validators=[
        validate_recurrence_pattern])
    recurrence_count = models.IntegerField(null=True, blank=True)
    recurrence_left = models.IntegerField(null=True, blank=True)
    created_by = models.CharField(max_length=7, default="unknown")
    created_at = models.DateTimeField()
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = TrialScheduleManager()

    def __init__(self, *args, **kwargs):
        super(TrialSchedule, self).__init__(*args, **kwargs)
        self._original_recurrence_count = self.recurrence_count

    def save(self, *args, **kwargs):
        self.update_metadata()

        if not self.created_at:
            self.created_at = timezone.now()
            self.recurrence_left = self.recurrence_count

        # update of recurrence_count
        if self.recurrence_count != self._original_recurrence_count:
            self.recurrence_left = self.recurrence_count
            self._original_recurrence_count = self.recurrence_count

        return super(TrialSchedule, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save()

    def has_recurrence_count_set(self) -> bool:
        return self.recurrence_count is not None

    def has_recurrence_left(self) -> bool:
        return self.recurrence_left and self.recurrence_left > 0

    def should_execute_at(self, datetime_at: datetime,
                          scheduler_interval_seconds: int) -> bool:
        if self.has_recurrence_count_set() and not self.has_recurrence_left():
            return False
        next_datetime = croniter(self.recurrence_pattern, datetime_at)\
            .get_next(ret_type=datetime)
        return scheduler_interval_seconds >= \
            (next_datetime - datetime_at).total_seconds()

    def decrement_recurrence_left(self):
        if self.has_recurrence_count_set() and self.has_recurrence_left():
            self.recurrence_left -= 1
            self.save()

    def update_metadata(self):
        temp_metadata = deepcopy(self.metadata)
        self.metadata = deepcopy(self.experiment.metadata)
        self.metadata.update(temp_metadata)
