from django.db import models


class SingletonManager(models.Manager):

    def get_queryset(self, **kwargs):
        return super(SingletonManager, self).get_queryset().filter(id=1)
