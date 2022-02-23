from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.query import QuerySet
from django.http import Http404
from kallisticore.models import Experiment
from kallisticore.models.trial_schedule import TrialSchedule
from kallisticore.serializers import TrialScheduleSerializer
from rest_framework import viewsets
from rest_framework.decorators import authentication_classes


@authentication_classes((settings.KALLISTI_API_AUTH_CLASS,))
class TrialScheduleViewSet(viewsets.ModelViewSet):
    queryset = TrialSchedule.objects.all()
    serializer_class = TrialScheduleSerializer
    permission_classes = (settings.KALLISTI_API_PERMISSION_CLASS,)

    def get_queryset(self):
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method."
                % self.__class__.__name__
        )
        if 'pk' in self.kwargs:
            queryset = TrialSchedule.objects.get_queryset_all(**self.kwargs)
        else:
            queryset = self.queryset.filter(**self.kwargs)

        if isinstance(queryset, QuerySet):
            queryset = queryset.all()

        return queryset

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self,
            'experiment_id': self.kwargs.get('experiment_id')
        }

    def create(self, request, *args, **kwargs):
        try:
            return super(TrialScheduleViewSet, self).create(request, *args,
                                                            **kwargs)
        except (IntegrityError, ValidationError, Experiment.DoesNotExist):
            raise Http404
