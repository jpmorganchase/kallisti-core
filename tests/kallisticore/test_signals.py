from unittest import mock

from django.test import TestCase
from kallisticore import signals
from kallisticore.models import Experiment
from kallisticore.models.step import Step
from kallisticore.models.trial import Trial
from kallisticore.signals import execute_plan_for_trial


class TestSignalExecutePlanForTrial(TestCase):

    def setUp(self):
        self.env = 'dev'
        self.step_to_get_app_by_name = {
            'step': 'Get CF App by Name',
            'do': 'cf.get_app_by_name',
            'where': {
                'app_name': 'hello-world',
                'cf_api_url': 'https://cf-api.test'
            }}
        self.test_k8s_step = {
            'step': 'K8s Test Step',
            'do': 'k8s.test_do',
            'where': {
                'where-key-1': 'where-value-1',
                'where-key-2': 'where-key-2'
            }}
        self._list_of_commands = [self.step_to_get_app_by_name,
                                  self.test_k8s_step]
        self._experiment = Experiment.create(
            name='test_experiment', description='detailed text description',
            steps=Step.convert_to_steps(self._list_of_commands))

    @mock.patch("kallisticore.signals.execute_trial")
    def test_executor_not_invoked_for_existing_trial(self, mock_exec_trial):
        trial = create_a_trial_object(self._experiment)
        trial.save()

        mock_exec_trial.assert_not_called()


def create_a_trial_object(experiment):
    signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)
    trial = Trial.create(experiment=experiment)
    signals.post_save.connect(execute_plan_for_trial, sender=Trial)
    return trial
