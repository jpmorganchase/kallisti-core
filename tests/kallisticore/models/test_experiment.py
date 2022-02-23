from django.test import TestCase

from kallisticore.models.experiment import Experiment
from kallisticore.models.step import Step


class TestExperiment(TestCase):
    def setUp(self):
        self.metadata = {"test_id": "123456"}
        self.parameters = {"org": "my-org",
                           "app_name": "hello-world",
                           "url": "https://app.test"}
        self.pre_steps = [{"step": "name",
                           "do": "cm.http_probe",
                           "where": {"url": "{{url}}"}}]
        self.steps = [{"step": "name",
                       "do": "cf.stop_app",
                       "where": {"app_name": "{{app_name}}",
                                 "org_name": "{{org}}"}}]
        self.post_steps = [{"step": "name",
                            "do": "cf.start_app",
                            "where": {"app_name": "{{app_name}}",
                                      "org_name": "{{org}}"}}]
        self.experiment = Experiment.create(
            name='one-action',
            description='one action description',
            metadata=self.metadata,
            pre_steps=Step.convert_to_steps(self.pre_steps),
            steps=Step.convert_to_steps(self.steps),
            post_steps=Step.convert_to_steps(self.post_steps),
            parameters=self.parameters
        )

    def test_experiment_fetch_all(self):
        experiments = Experiment.objects.all()
        self.assertEqual(len(experiments), 1)

        experiment = experiments[0]
        self.assertIsNotNone(experiment.id)
        self.assertEqual(experiment.description, "one action description")
        self.assertEqual(Step.convert_to_steps(self.steps), experiment.steps)
        self.assertEqual(Step.convert_to_steps(self.pre_steps),
                         experiment.pre_steps)
        self.assertEqual(Step.convert_to_steps(self.post_steps),
                         experiment.post_steps)
        self.assertEqual(experiment.parameters, self.parameters)
        self.assertEqual(experiment.metadata, self.metadata)
        self.assertEqual(experiment.created_by, "unknown")

    def test_experiment_soft_delete_fetch_all(self):
        go_web_experiments = Experiment.objects.all()
        self.assertEqual(len(go_web_experiments), 1)

        Experiment.objects.get(name='one-action').delete()
        go_web_experiments = Experiment.objects.all()
        self.assertEqual(len(go_web_experiments), 0)

    def test_experiment_fetch(self):
        experiment = Experiment.objects.get(name='one-action')
        self.assertIsNotNone(experiment.id)
        self.assertEqual(experiment.description, "one action description")
        self.assertEqual(Step.convert_to_steps(self.pre_steps),
                         experiment.pre_steps)
        self.assertEqual(Step.convert_to_steps(self.steps), experiment.steps)
        self.assertEqual(Step.convert_to_steps(self.post_steps),
                         experiment.post_steps)
        self.assertEqual(experiment.parameters, self.parameters)
        self.assertEqual(experiment.metadata, self.metadata)
        self.assertEqual(experiment.created_by, "unknown")

    def test_experiment_soft_delete_fetch(self):
        experiment = Experiment.objects.get(name='one-action')
        self.assertIsNotNone(experiment.id)

        experiment.delete()

        # objects.get should raise an DoesNotExist error
        with self.assertRaises(Experiment.DoesNotExist):
            Experiment.objects.get(id=experiment.id)

        # objects.get_queryset_all().get() should return the deleted experiment
        experiment = Experiment.objects.get_queryset_all().get(
            id=experiment.id)
        self.assertIsNotNone(experiment.id)
        self.assertEqual(experiment.description, "one action description")
        self.assertEqual(Step.convert_to_steps(self.pre_steps),
                         experiment.pre_steps)
        self.assertEqual(Step.convert_to_steps(self.steps), experiment.steps)
        self.assertEqual(Step.convert_to_steps(self.post_steps),
                         experiment.post_steps)
        self.assertEqual(experiment.parameters, self.parameters)
        self.assertEqual(experiment.metadata, self.metadata)
        self.assertEqual(experiment.created_by, "unknown")
