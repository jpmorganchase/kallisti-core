from django.conf import settings
from rest_framework import status
from rest_framework.decorators import authentication_classes
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from kallisticore.models import Trial
from kallisticore.models.trial import TrialStatus
from kallisticore.serializers import TrialSerializer


@authentication_classes((settings.KALLISTI_API_AUTH_CLASS,))
class TrialStopAPI(APIView):

    def put(self, request, trial_id):
        trial = get_object_or_404(Trial.objects, id=trial_id)
        trial_status = trial.get_status()
        if trial_status == TrialStatus.STOP_INITIATED.value:
            return Response(TrialSerializer(trial).data)
        if trial_status not in [TrialStatus.SCHEDULED.value,
                                TrialStatus.IN_PROGRESS.value]:
            return Response(
                data={"message": "Trial has either not started or already set "
                                 "to stop."},
                status=status.HTTP_403_FORBIDDEN)
        trial.update_status(TrialStatus.STOP_INITIATED)
        trial = Trial.objects.get(id=trial_id)
        return Response(TrialSerializer(trial).data)
