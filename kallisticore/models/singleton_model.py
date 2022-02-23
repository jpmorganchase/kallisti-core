from django.db import models


class SingletonModel(models.Model):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls.objects.create(*args, **kwargs)

    @classmethod
    def delete(cls, *args, **kwargs):
        return cls.objects.filter(pk=1).delete()

    class Meta:
        abstract = True
