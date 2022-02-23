from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from kallisticore.views.experiment import ExperimentViewSet
from kallisticore.views.report import ReportAPI
from kallisticore.views.trial import TrialViewSet
from kallisticore.views.trial_schedule import TrialScheduleViewSet

router = DefaultRouter()
router.register(r'experiment', ExperimentViewSet)
router.register(r'trial', TrialViewSet)
router.register(r'experiment/(?P<experiment_id>[-\w]+)/schedule',
                TrialScheduleViewSet, 'trial-schedule')

urlpatterns = [
    url(r'^report', ReportAPI.as_view(), name='report'),
    url(r'^', include(router.urls))
]
