from django.db import models

from kallisticore.models.singleton_model import SingletonModel
from kallisticore.models.singleton_manager import SingletonManager
from kallisticore.utils.fields import ListField


class Notification(SingletonModel):
    id = models.AutoField(primary_key=True, editable=False)
    emails = ListField(default=[])

    objects = SingletonManager()

    class Meta:
        verbose_name = "Notification"
