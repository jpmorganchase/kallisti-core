from django.urls import reverse
from rest_framework import status

from kallisticore.models import Experiment, Trial
from kallisticore.serializers import ReportSerializer
from kallisticore.views.report import trial_id_query_param
from tests.kallisticore.base import KallistiTestSuite


class TestQueryParam(KallistiTestSuite):

    def test_trial_id_query_param(self):
        self.assertEqual(trial_id_query_param.name, 'trial-id')
        self.assertEqual(trial_id_query_param.in_, 'query')
        self.assertEqual(trial_id_query_param.description,
                         '[Optional] A UUID string identifying a trial to get '
                         'report for the trial')
        self.assertEqual(trial_id_query_param.type, 'string')


class TestReportAPI(KallistiTestSuite):

    def setUp(self):
        super(TestReportAPI, self).setUp()
        self._token = 'test-token'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)

    def tearDown(self):
        self.client.credentials()
        super(TestReportAPI, self).tearDown()

    def test_list_report_empty_experiment(self):
        url = reverse('report')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_report_experiments_without_trials(self):
        experiment1 = Experiment.create(
            name='kill-my-web-cf-app-instance', description='HA experiment')
        experiment2 = Experiment.create(
            name='stop-my-web-cf-app', description='DR experiment')

        url = reverse('report')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.data
        self.assertEqual(len(response_data), 2)
        self.assertIn(ReportSerializer(experiment1).data, response_data)
        self.assertIn(ReportSerializer(experiment2).data, response_data)

    def test_list_report_experiments_with_trials(self):
        experiment = Experiment.create(
            name='kill-my-web-cf-app-instance', description='HA experiment')

        Trial.create(experiment=experiment)

        url = reverse('report')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.data
        self.assertEqual(len(response_data), 1)
        self.assertIn(ReportSerializer(experiment).data, response_data)
        self.assertEqual(ReportSerializer(experiment).data['trials'][0]['id'],
                         response_data[0]['trials'][0]['id'])

    def test_get_report_by_trial_id(self):
        experiment_1 = Experiment.create(name='test-experiment-1',
                                         description='Test experiment 1.')
        # make sure report is generated only for only corresponding experiment
        Experiment.create(name='test-experiment-2',
                          description='Test experiment 2.')

        trial = Trial.create(experiment=experiment_1)
        query_param = '?trial-id=%s' % trial.id
        # make sure report is generated only for only specified trial
        Trial.create(experiment=experiment_1)

        url = reverse('report')
        response = self.client.get(url + query_param, format='json')

        expected_report_serializer = ReportSerializer(experiment_1, context={
            'trial_id': trial.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.data
        self.assertEqual(len(response_data), 1)
        self.assertIn(expected_report_serializer.data, response_data)
        self.assertEqual(expected_report_serializer.data['trials'][0]['id'],
                         response_data[0]['trials'][0]['id'])
