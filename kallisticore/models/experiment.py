from uuid import uuid4

from django.db import models
from django.utils import timezone
from kallisticore.models.base_model import BaseModel
from kallisticore.utils.fields import DictField, StepsField


class ExperimentManager(models.Manager):

    def get_queryset(self, **kwargs):
        return super(ExperimentManager, self).get_queryset().filter(
            deleted_at=None, **kwargs)

    def get_queryset_all(self, **kwargs):
        return super(ExperimentManager, self).get_queryset().filter(**kwargs)


class Experiment(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=150, blank=False)
    description = models.TextField(blank=True)
    metadata = DictField(default={}, blank=True)
    pre_steps = StepsField(default=[])
    steps = StepsField(default=[])
    post_steps = StepsField(default=[])
    parameters = DictField(default={})
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=7, default="unknown")

    objects = ExperimentManager()

    class Meta:
        verbose_name = "Experiment"

    def delete(self):
        current_datetime = timezone.now()
        from kallisticore.models.trial_schedule import TrialSchedule
        TrialSchedule.objects.filter(experiment_id=self.id).update(
            deleted_at=current_datetime)
        self.deleted_at = current_datetime
        self.save()
