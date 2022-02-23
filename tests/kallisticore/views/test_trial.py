from unittest import mock

from django.urls import reverse
from rest_framework import status

import kallisticore
from kallisticore import signals
from kallisticore.authentication import KallistiUser
from kallisticore.models import Experiment, Trial
from kallisticore.models.step import Step
from kallisticore.serializers import TrialSerializer
from kallisticore.signals import execute_plan_for_trial
from tests.kallisticore.base import KallistiTestSuite


class TestTrialListAPI(KallistiTestSuite):

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
        super(TestTrialListAPI, self).setUp()
        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)

    def tearDown(self):
        self.client.credentials()
        super(TestTrialListAPI, self).tearDown()
        signals.post_save.connect(execute_plan_for_trial, sender=Trial)

    def test_list_empty_trial(self):
        url = reverse('trial-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_trials(self):
        trial = Trial.create(experiment=self._experiment,
                             parameters=self.parameters)

        url = reverse('trial-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.data
        self.assertEqual(len(response_data), 1)
        self.assertIn(TrialSerializer(trial).data, response_data)

    def test_list_trials_with_soft_deleted_experiment(self):
        Trial.create(experiment=self._experiment, parameters=self.parameters)

        self._experiment.delete()

        url = reverse('trial-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.data
        self.assertEqual(len(response_data), 0)


class TestTrialGetAPI(KallistiTestSuite):

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
        super(TestTrialGetAPI, self).setUp()
        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)

    def tearDown(self):
        self.client.credentials()
        super(TestTrialGetAPI, self).tearDown()
        signals.post_save.connect(execute_plan_for_trial, sender=Trial)

    def test_get_trial_details(self):
        trial = Trial.create(experiment=self._experiment,
                             parameters=self.parameters)

        url = reverse('trial-detail', args=[trial.id])
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.data
        self.assertEqual(TrialSerializer(trial).data, response_data)

    def test_get_non_existing_trial(self):
        url = reverse('trial-detail', args=['notexists'])
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

    @mock.patch.object(kallisticore.authentication.DefaultAuthentication,
                       "authenticate",
                       return_value=(KallistiUser(user_id='f123456'), None))
    def test_initiated_by_on_post(self, _):
        url = reverse('trial-list')
        response = self.client.post(url, format='json', data={
            'experiment': str(self._experiment.id)
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.data
        self.assertEqual('f123456', response_data['initiated_by'])

    def test_get_trial_with_soft_deleted_experiment(self):
        trial = Trial.create(experiment=self._experiment,
                             parameters=self.parameters)

        self._experiment.delete()

        url = reverse('trial-detail', args=[trial.id])
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.data
        self.assertEqual(TrialSerializer(trial).data, response_data)


class TestTrialCreateAPI(KallistiTestSuite):
    def setUp(self):
        super(TestTrialCreateAPI, self).setUp()
        self._token = '123123123123123'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)

        signals.post_save.disconnect(execute_plan_for_trial, sender=Trial)

        self._experiment = Experiment.create()

    def tearDown(self):
        self.client.credentials()
        super(TestTrialCreateAPI, self).tearDown()
        signals.post_save.connect(execute_plan_for_trial, sender=Trial)

    def test_create(self):
        data = {'experiment': self._experiment.id}
        url = reverse('trial-list')
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Trial.objects.count(), 1)

    def test_create_for_deleted_experiment(self):
        data = {'experiment': self._experiment.id}
        self._experiment.delete()
        url = reverse('trial-list')
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Trial.objects.count(), 0)
