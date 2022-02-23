from django.conf import settings
from django.db.models.query import QuerySet
from kallisticore.models.experiment import Experiment
from kallisticore.serializers import ExperimentSerializer
from rest_framework import viewsets
from rest_framework.decorators import authentication_classes


@authentication_classes((settings.KALLISTI_API_AUTH_CLASS,))
class ExperimentViewSet(viewsets.ModelViewSet):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
    permission_classes = (settings.KALLISTI_API_PERMISSION_CLASS,)

    def get_queryset(self):
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, or "
                "override the `get_queryset()` method."
                % self.__class__.__name__
        )

        if 'pk' in self.kwargs:
            # Get all including deleted experiments if queried by primary key
            queryset = Experiment.objects.get_queryset_all(**self.kwargs)
        else:
            queryset = self.queryset.filter(**self.kwargs)

        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request
            queryset = queryset.all()

        return queryset
