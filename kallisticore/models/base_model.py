from django.db import models


class BaseModel(models.Model):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls.objects.create(*args, **kwargs)

    class Meta:
        abstract = True
