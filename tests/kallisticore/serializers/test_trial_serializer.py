from collections import OrderedDict

from django.db.models.signals import post_save
from django.test import TestCase

from kallisticore.models import Trial
from kallisticore.models.experiment import Experiment
from kallisticore.models.trial import TrialStatus
from kallisticore.serializers import TrialSerializer
from kallisticore.signals import execute_plan_for_trial


class TestTrialSerializer(TestCase):
    def setUp(self):
        self._experiment = Experiment.create(
            name='kill-my-web-cf-app-instance',
            description='detailed text description',
            parameters={'space': 'dev', 'org': 'my-org'},
            metadata={'job_id': '12345'},
            steps=[{'do': 'Kill CF Instance',
                    'where': {'space_name': 'dev',
                              'org_name': 'my-org',
                              'instances_to_kill': 0}}])

        post_save.disconnect(execute_plan_for_trial, sender=Trial)

        self._trial = Trial.create(
            experiment=self._experiment,
            metadata={'trial_name': 'hello_world'}, initiated_by='user-a',
            records='{"steps": [{"logs": ["test", "test1"]}]}')

    def tearDown(self):
        post_save.connect(execute_plan_for_trial, sender=Trial)

    def test_trial_serialization(self):
        serializer = TrialSerializer(self._trial)
        data = serializer.data

        self.assertEqual(11, len(data))
        self.assertIsNotNone(data['id'])
        self.assertEqual(Experiment.objects.get(id=data['experiment']),
                         self._experiment)
        self.assertEqual(data['parameters'], {})
        self.assertEqual(data['ticket'], {})
        self.assertEqual(data['metadata'],
                         {'job_id': '12345', 'trial_name': 'hello_world'})
        self.assertEqual(data['trial_record'],
                         OrderedDict(
                             [('steps', [{'logs': ['test', 'test1']}])]))
        self.assertEqual(data['status'], TrialStatus.SCHEDULED.value)
        self.assertEqual(data['executed_at'], self._trial.executed_at)
        self.assertEqual(data['completed_at'], None)
        self.assertEqual(data['initiated_by'], 'user-a')
