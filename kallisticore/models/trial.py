from copy import deepcopy
from enum import Enum
from typing import Set
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from kallisticore.models.base_model import BaseModel
from kallisticore.models.experiment import Experiment
from kallisticore.models.step import Step
from kallisticore.utils.fields import DictField


class TrialStepsType(Enum):
    PRE = "pre_steps"
    STEPS = "steps"
    POST = "post_steps"


class TrialStatus(Enum):
    FAILED = "Failed"
    SUCCEEDED = "Succeeded"
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    ABORTED = "Aborted"
    INVALID = "Invalid"
    STOP_INITIATED = "Stop Initiated"
    STOPPED = "Stopped"


ALLOWED_TRIAL_TICKET_KEYS = getattr(
    settings, 'KALLISTI_ALLOWED_TRIAL_TICKET_TYPES', [])


def validate_trial_status(trial_status_value):
    if trial_status_value in [status.value for status in TrialStatus]:
        return True
    raise ValidationError("%(value)s is not a valid trial status",
                          params={'value': trial_status_value})


def validate_trial_ticket(trial_ticket):
    if {'type', 'number'} == set(trial_ticket) and \
            trial_ticket['type'] in ALLOWED_TRIAL_TICKET_KEYS:
        return True
    raise ValidationError("%(value)s is not a valid trial ticket",
                          params={'value': trial_ticket})


class TrialManager(models.Manager):
    def get_queryset(self, **kwargs):
        return super(TrialManager, self).get_queryset().filter(
            experiment__deleted_at=None, **kwargs)

    def get_queryset_all(self, **kwargs):
        return super(TrialManager, self).get_queryset().filter(**kwargs)


class Trial(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    experiment = models.ForeignKey(Experiment, related_name="trials",
                                   on_delete=models.DO_NOTHING)
    parameters = DictField(default={}, blank=True)
    metadata = DictField(default={}, blank=True)
    ticket = DictField(default={}, blank=True,
                       validators=[validate_trial_ticket])
    initiated_by = models.CharField(max_length=32, default="unknown")
    initiated_from = models.CharField(max_length=20, default="unknown")
    status = models.CharField(max_length=20,
                              default=TrialStatus.SCHEDULED.value,
                              validators=[validate_trial_status])
    executed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records = DictField(default={}, blank=True)

    objects = TrialManager()

    def update_status(self, trial_status: TrialStatus) -> None:
        self.status = trial_status.value
        if self.status == TrialStatus.SUCCEEDED.value or \
                self.status == TrialStatus.FAILED.value or \
                self.status == TrialStatus.ABORTED.value or \
                self.status == TrialStatus.INVALID.value:
            self.completed_at = timezone.datetime.now()
        self.save()

    def get_status(self) -> TrialStatus:
        return Trial.objects.get(id=self.id).status

    def update_executed_at(self) -> None:
        self.executed_at = timezone.datetime.now()
        self.save()

    def get_undefined_variables(self) -> Set[str]:
        undefined_variables = self._get_undefined_variables(
            self.experiment.steps)
        undefined_variables.update(
            self._get_undefined_variables(self.experiment.pre_steps))
        undefined_variables.update(
            self._get_undefined_variables(self.experiment.post_steps))
        return undefined_variables

    def _get_undefined_variables(self, steps):
        undefined_variables = set()
        for step in steps:
            variables = step.get_where_clause_template_variables()
            for variable in variables:
                if variable not in self.get_populated_parameters():
                    undefined_variables.add(variable)
        return undefined_variables

    def get_populated_parameters(self):
        experiment_parameters = self.experiment.parameters
        if experiment_parameters:
            experiment_parameters.update(self.parameters)
            return experiment_parameters
        else:
            return self.parameters

    def get_steps(self) -> [Step]:
        steps = deepcopy(self.experiment.steps)
        for step in steps:
            step.interpolate_with_parameters(self.get_populated_parameters())
        return steps

    def get_post_steps(self) -> [Step]:
        steps = deepcopy(self.experiment.post_steps)
        for step in steps:
            step.interpolate_with_parameters(self.get_populated_parameters())
        return steps

    def get_pre_steps(self) -> [Step]:
        steps = deepcopy(self.experiment.pre_steps)
        for step in steps:
            step.interpolate_with_parameters(self.get_populated_parameters())
        return steps

    def update_metadata(self):
        temp_metadata = deepcopy(self.metadata)
        self.metadata = deepcopy(self.experiment.metadata)
        self.metadata.update(temp_metadata)

    def save(self, *args, **kwargs):
        self.update_metadata()
        super(Trial, self).save(*args, **kwargs)

    def is_completed(self):
        return not not self.completed_at
