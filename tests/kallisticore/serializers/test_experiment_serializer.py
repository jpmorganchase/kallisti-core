from django.test import TestCase

from kallisticore.models.experiment import Experiment
from kallisticore.serializers import ExperimentSerializer


class TestExperimentSerializer(TestCase):

    def test_experiment_fetch(self):
        name = 'kill-hello-world-cf-app-instance'
        description = 'detailed text description'
        metadata = {'meta_data': '123456'}
        parameters = {'space': 'dev',
                      'app_name': 'hello-world',
                      'org': 'MY-ORG'}
        pre_steps = [{'step': 'name',
                      'do': 'cm.http_probe',
                      'where': {'url': 'https://hello-world.test.com'}}]
        steps = [{'do': 'cf.stop_app',
                  'where': {'space': 'dev', 'app_name': 'hello-world'},
                  }]
        post_steps = [{'do': 'cf.start_app',
                       'where': {'space': 'dev', 'app_name': 'hello-world'},
                       }]
        experiment = Experiment.create(name=name,
                                       description=description,
                                       metadata=metadata,
                                       parameters=parameters,
                                       pre_steps=pre_steps,
                                       steps=steps,
                                       post_steps=post_steps,
                                       created_by='user-a')

        serializer = ExperimentSerializer(experiment)
        experiment_data = serializer.data

        self.assertIsNotNone(experiment_data['id'])
        self.assertEqual(experiment_data['name'], name)
        self.assertEqual(experiment_data['description'], description)
        self.assertEqual(experiment_data['pre_steps'], pre_steps)
        self.assertEqual(experiment_data['steps'], steps)
        self.assertEqual(experiment_data['post_steps'], post_steps)
        self.assertEqual(experiment_data['parameters'], parameters)
        self.assertEqual(experiment_data['metadata'], metadata)
        self.assertEqual(experiment_data['created_by'], 'user-a')
