from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from kallisticore.models import Experiment, Trial
from kallisticore.renderers import XMLRenderer
from kallisticore.serializers import ReportSerializer
from rest_framework.decorators import authentication_classes
from rest_framework.generics import ListAPIView, get_object_or_404

trial_id_query_param = openapi.Parameter(
    'trial-id', openapi.IN_QUERY,
    '[Optional] A UUID string identifying a trial to get report for the trial',
    type=openapi.TYPE_STRING)


@authentication_classes((settings.KALLISTI_API_AUTH_CLASS,))
class ReportAPI(ListAPIView):
    queryset = Experiment.objects.all()
    serializer_class = ReportSerializer
    renderer_classes = (XMLRenderer,)
    permission_classes = (settings.KALLISTI_API_PERMISSION_CLASS,)

    @swagger_auto_schema(manual_parameters=[trial_id_query_param])
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        trial_id = request.query_params.get('trial-id')
        if trial_id:
            trial = get_object_or_404(Trial.objects, id=trial_id)
            self.queryset = [trial.experiment]
        return super(ListAPIView, self).list(request, *args, **kwargs)

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self,
            'trial_id': self.request.query_params.get('trial-id')
        }
