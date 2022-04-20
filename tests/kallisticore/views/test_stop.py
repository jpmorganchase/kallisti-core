from django.urls import reverse

from rest_framework import status

from kallisticore import signals
from kallisticore.models.step import Step
from kallisticore.models import Experiment, Trial
from kallisticore.models.trial import TrialStatus
from kallisticore.signals import execute_plan_for_trial
from tests.kallisticore.base import KallistiTestSuite


class TestStopAPI(KallistiTestSuite):
    def setUp(self):
        self._token = '123123123123123'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)

        self.parameters = {"org": "MY-ORG",
                           "app_name": "hello-world"}
        self.steps = [{"step": "name",
                       "do": "cf.stop_app",
                       "where": {"app_name": "{{app_name}}",
                                 "org_name": "{{org}}"}}]
        self.post_steps = [{"step": "name",
                            "do": "cf.start_app",
                            "where": {"app_name": "{{app_name}}",
                                      "org_name": "{{org}}"}}]
        self._experiment = Experiment.create(
            name='one-action',
            description='one action description',
            steps=Step.convert_to_steps(self.steps),
            post_steps=Step.convert_to_steps(self.post_steps),
        )
        super(TestStopAPI, self).setUp()
        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)

    def tearDown(self):
        self.client.credentials()
        super(TestStopAPI, self).tearDown()
        signals.post_save.connect(execute_plan_for_trial, sender=Trial)

    def test_stop_status(self):
        """
        Stop a trial
        """
        trial = Trial.create(experiment=self._experiment,
                             parameters=self.parameters)
        url = reverse('trial-stop', kwargs={'trial_id': trial.id})
        response = self.client.put(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'],
                         TrialStatus.STOP_INITIATED.value)

    def test_trial_already_started(self):
        """
        Should return 200 if trial has already set to stop
        """
        trial = Trial.create(experiment=self._experiment,
                             parameters=self.parameters)
        trial.update_status(TrialStatus.STOP_INITIATED)
        url = reverse('trial-stop', kwargs={'trial_id': trial.id})
        response = self.client.put(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'],
                         TrialStatus.STOP_INITIATED.value)

    def test_trial_not_started(self):
        """
        Should return 403 if trial is not in SCHEDULED or IN_PROGRESS
        """
        trial = Trial.create(experiment=self._experiment,
                             parameters=self.parameters)
        trial.update_status(TrialStatus.STOPPED)
        url = reverse('trial-stop', kwargs={'trial_id': trial.id})
        response = self.client.put(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['message'],
                         'Trial has either not started or already set to '
                         'stop.')

    def test_no_trial_id(self):
        """
        Should return 404 if trial id does not exist
        """
        url = reverse('trial-stop', kwargs={'trial_id': 'test-trial-id'})
        response = self.client.put(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
