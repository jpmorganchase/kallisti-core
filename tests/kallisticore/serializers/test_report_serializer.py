from django.db.models.signals import post_save
from django.test import TestCase

from kallisticore.models import Trial
from kallisticore.models.experiment import Experiment
from kallisticore.models.trial import TrialStatus
from kallisticore.serializers import ReportSerializer
from kallisticore.signals import execute_plan_for_trial


class TestReportSerializer(TestCase):

    def setUp(self):
        self.name = 'kill-hello-world-cf-app-instance'
        self.description = 'detailed text description'
        self.parameters = {'space': 'dev',
                           'app_name': 'hello-world',
                           'org': 'CAF-ORG'}
        self.experiment_metadata = {'example_meta': '123456'}
        self.trial_metadata = {'trial_data': 'hello_world'}
        self.pre_steps = [{'step': 'name',
                           'do': 'cm.http_probe',
                           'where': {'url': 'https://hello-world.test.com'}}]
        self.steps = [{'do': 'cf.stop_app',
                       'where': {'space': 'test', 'app_name': 'hello-world'},
                       }]
        self.post_steps = [{'do': 'cf.start_app',
                            'where': {'space': 'dev',
                                      'app_name': 'hello-world',
                                      'org': 'MY-ORG'}}]
        self.experiment = Experiment.create(name=self.name,
                                            description=self.description,
                                            parameters=self.parameters,
                                            pre_steps=self.pre_steps,
                                            steps=self.steps,
                                            post_steps=self.post_steps)

        post_save.disconnect(execute_plan_for_trial, sender=Trial)
        self.trial = Trial.create(experiment=self.experiment,
                                  records='{"steps": {}}')

    def tearDown(self):
        post_save.connect(execute_plan_for_trial, sender=Trial)

    def test_report_serialization(self):
        serializer = ReportSerializer(self.experiment)
        data = serializer.data

        self.assertEqual(9, len(data))
        self.assertIsNotNone(data['id'])
        self.assertEqual(data['name'], self.name)
        self.assertEqual(data['description'], self.description)
        self.assertEqual(data['pre_steps'], self.pre_steps)
        self.assertEqual(data['steps'], self.steps)
        self.assertEqual(data['post_steps'], self.post_steps)
        self.assertEqual(data['parameters'], self.parameters)
        self.assertEqual(data['trials'][0]['trial_record'], {'steps': {}})
        self.assertEqual(data['trials'][0]['status'],
                         TrialStatus.SCHEDULED.value)
        self.assertEqual(data['trials'][0]['executed_at'],
                         self.trial.executed_at)

    def test_report_serialization_with_query_param(self):
        # make sure serialized experiment has only specified trial
        Trial.create(experiment=self.experiment)

        report_serializer = ReportSerializer(
            self.experiment, context={'trial_id': self.trial.id})
        data = report_serializer.data

        self.assertEqual(9, len(data))
        self.assertIsNotNone(data['id'])
        self.assertEqual(data['name'], self.name)
        self.assertEqual(data['description'], self.description)
        self.assertEqual(data['steps'], self.steps)
        self.assertEqual(data['pre_steps'], self.pre_steps)
        self.assertEqual(data['post_steps'], self.post_steps)
        self.assertEqual(data['parameters'], self.parameters)
        self.assertEqual(len(data['trials']), 1)
        self.assertEqual(data['trials'][0]['trial_record'], {'steps': {}})
        self.assertEqual(data['trials'][0]['status'],
                         TrialStatus.SCHEDULED.value)
        self.assertEqual(data['trials'][0]['executed_at'],
                         self.trial.executed_at)

    def test_report_serialization_with_metadata(self):
        experiment = Experiment.create(name=self.name,
                                       description=self.description,
                                       parameters=self.parameters,
                                       metadata=self.experiment_metadata,
                                       pre_steps=self.pre_steps,
                                       steps=self.steps,
                                       post_steps=self.post_steps)
        trial = Trial.create(experiment=experiment,
                             metadata=self.trial_metadata)
        report_serializer = ReportSerializer(experiment,
                                             context={'trial_id': trial.id})
        data = report_serializer.data
        self.assertEqual(9, len(data))
        self.assertIsNotNone(data['id'])
        self.assertEqual(data['name'], self.name)
        self.assertEqual(data['description'], self.description)
        self.assertEqual(data['metadata'], self.experiment_metadata)
        self.assertEqual(data['pre_steps'], self.pre_steps)
        self.assertEqual(data['steps'], self.steps)
        self.assertEqual(data['post_steps'], self.post_steps)
        self.assertEqual(data['parameters'], self.parameters)
        self.assertEqual(len(data['trials']), 1)
        self.assertEqual(data['trials'][0]['status'],
                         TrialStatus.SCHEDULED.value)
        self.assertEqual(data['trials'][0]['executed_at'],
                         self.trial.executed_at)
        self.assertEqual(data['trials'][0]['metadata'],
                         {'example_meta': '123456',
                          'trial_data': 'hello_world'})
