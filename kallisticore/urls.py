from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from kallisticore.views.experiment import ExperimentViewSet
from kallisticore.views.report import ReportAPI
from kallisticore.views.trial import TrialViewSet
from kallisticore.views.trial_schedule import TrialScheduleViewSet
from kallisticore.views.trial_stop import TrialStopAPI
from kallisticore.views.notification import NotificationViewSet

router = DefaultRouter()
router.register(r'experiment', ExperimentViewSet)
router.register(r'trial', TrialViewSet)
router.register(r'experiment/(?P<experiment_id>[-\w]+)/schedule',
                TrialScheduleViewSet, 'trial-schedule')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^report', ReportAPI.as_view(), name='report'),
    url(r'^notification', NotificationViewSet.as_view(
        {'get': 'list', 'put': 'update'}), name='notification'),
    url(r'trial/(?P<trial_id>[-\w]+)/stop', TrialStopAPI.as_view(),
        name='trial-stop'),
]
