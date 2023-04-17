from django.urls import reverse
from kallisticore.models.experiment import Experiment
from kallisticore.serializers import ExperimentSerializer
from rest_framework import status
from tests.kallisticore.base import KallistiTestSuite
from uuid import uuid4


class TestExperimentListAPI(KallistiTestSuite):

    def setUp(self):
        super(TestExperimentListAPI, self).setUp()
        self._token = '123123123123123'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)

    def tearDown(self):
        self.client.credentials()
        super(TestExperimentListAPI, self).tearDown()

    def test_list_empty_experiments(self):
        url = reverse('experiment-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_experiments(self):
        experiment1 = Experiment.create(
            name='kill-my-web-cf-app-instance', description='HA experiment')
        experiment2 = Experiment.create(
            name='stop-my-web-cf-app', description='DR experiment')

        url = reverse('experiment-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.data
        self.assertEqual(len(response_data), 2)
        self.assertIn(ExperimentSerializer(experiment1).data, response_data)
        self.assertIn(ExperimentSerializer(experiment2).data, response_data)


class TestExperimentGetAPI(KallistiTestSuite):
    def setUp(self):
        super(TestExperimentGetAPI, self).setUp()
        self._token = '123123123123123'
        self._non_existent = uuid4()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)

    def tearDown(self):
        self.client.credentials()
        super(TestExperimentGetAPI, self).tearDown()

    def test_get_details_with_invalid_id(self):
        url = reverse('experiment-detail', args=[self._non_existent])
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

    def test_get_details(self):
        experiment = Experiment.create(
            name='kill-my-web-cf-app-instance', description='HA experiment')

        url = reverse('experiment-detail', args=[experiment.id])
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, ExperimentSerializer(experiment).data)


class TestExperimentCreateAPI(KallistiTestSuite):
    def setUp(self):
        super(TestExperimentCreateAPI, self).setUp()
        self._token = '123123123123123'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)

    def tearDown(self):
        self.client.credentials()
        super(TestExperimentCreateAPI, self).tearDown()

    def test_post_with_valid_details(self):
        data = {'name': 'go-redirection-would-work-when-database-dies',
                'description': 'This experiment would prove go redirection '
                               'would be resilient to DB failures',
                'parameters': {},
                'steps': []}
        url = reverse('experiment-list')

        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Experiment.objects.count(), 1)

    def test_post_with_invalid_data(self):
        url = reverse('experiment-list')
        response = self.client.post(url, data={}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Experiment.objects.count(), 0)


class TestExperimentDeleteAPI(KallistiTestSuite):
    def setUp(self):
        super(TestExperimentDeleteAPI, self).setUp()
        self._token = '123123123123123'
        self._non_existent = uuid4()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)

    def tearDown(self):
        self.client.credentials()
        super(TestExperimentDeleteAPI, self).tearDown()

    def test_delete_with_invalid_id(self):
        url = reverse('experiment-detail', args=[self._non_existent])
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

    def test_delete(self):
        experiment = Experiment.create(
            name='kill-my-web-cf-app-instance', description='HA experiment')

        url = reverse('experiment-detail', args=[experiment.id])
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Experiment.objects.count(), 0)


class TestExperimentPatchAPI(KallistiTestSuite):
    def setUp(self):
        super(TestExperimentPatchAPI, self).setUp()
        self._data = {'description': 'This experiment would prove go '
                                     'redirection would be resilient to DB '
                                     'failures'}
        self._token = '123123123123123'
        self._non_existent = uuid4()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)

    def tearDown(self):
        self.client.credentials()
        super(TestExperimentPatchAPI, self).tearDown()

    def test_patch_with_invalid_id(self):
        url = reverse('experiment-detail', args=[self._non_existent])
        response = self.client.patch(url, data=self._data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

    def test_patch(self):
        experiment = Experiment.create(
            name='kill-my-web-cf-app-instance', description='HA experiment')

        url = reverse('experiment-detail', args=[experiment.id])
        response = self.client.patch(url, data=self._data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Experiment.objects.count(), 1)
