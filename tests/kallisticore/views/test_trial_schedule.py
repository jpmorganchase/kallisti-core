from django.urls import reverse
from kallisticore.models import Experiment
from kallisticore.models.trial_schedule import TrialSchedule
from kallisticore.serializers import TrialScheduleSerializer
from rest_framework import status
from tests.kallisticore.base import KallistiTestSuite
from uuid import uuid4


class TestTrialScheduleListAPI(KallistiTestSuite):

    def setUp(self):
        self._token = 'test-token'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)

        self._experiment = Experiment.create()
        super(TestTrialScheduleListAPI, self).setUp()

    def tearDown(self):
        self.client.credentials()
        super(TestTrialScheduleListAPI, self).tearDown()

    def test_list_empty_schedule(self):
        url = reverse('trial-schedule-list',
                      kwargs={'experiment_id': self._experiment.id})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_schedules(self):
        trial_schedule = TrialSchedule.create(
            experiment=self._experiment,
            recurrence_pattern='* * * * *'
        )

        url = reverse('trial-schedule-list',
                      kwargs={'experiment_id': self._experiment.id})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.data
        self.assertEqual(len(response_data), 1)
        self.assertIn(TrialScheduleSerializer(trial_schedule).data,
                      response_data)

    def test_list_schedules_with_deleted_experiment(self):
        TrialSchedule.create(
            experiment=self._experiment,
            recurrence_pattern='* * * * *'
        )
        self._experiment.delete()

        url = reverse('trial-schedule-list',
                      kwargs={'experiment_id': self._experiment.id})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.data
        self.assertEqual(len(response_data), 0)


class TestTrialScheduleDetailAPI(KallistiTestSuite):

    def setUp(self):
        self._token = '123123123123123'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)
        self._non_existing_pk = uuid4()
        self._non_existing_experiment_id = uuid4()
        self._experiment = Experiment.create()
        super(TestTrialScheduleDetailAPI, self).setUp()

    def tearDown(self):
        self.client.credentials()
        super(TestTrialScheduleDetailAPI, self).tearDown()

    def test_detail_with_non_existing_pk(self):
        url = reverse('trial-schedule-detail',
                      kwargs={'experiment_id': self._experiment.id,
                              'pk': self._non_existing_pk})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_with_non_existing_experiment_id(self):
        trial_schedule = TrialSchedule.create(
            experiment=self._experiment,
            recurrence_pattern='* * * * *'
        )
        url = reverse('trial-schedule-detail',
                      kwargs={'experiment_id': self._non_existing_experiment_id,
                              'pk': trial_schedule.id})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_entry(self):
        trial_schedule = TrialSchedule.create(
            experiment=self._experiment,
            recurrence_pattern='* * * * *'
        )

        url = reverse('trial-schedule-detail',
                      kwargs={'experiment_id': self._experiment.id,
                              'pk': trial_schedule.id})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = [response.data]
        self.assertEqual(len(response_data), 1)
        self.assertIn(TrialScheduleSerializer(trial_schedule).data,
                      response_data)

    def test_detail_with_soft_deleted_experiment(self):
        trial_schedule = TrialSchedule.create(
            experiment=self._experiment,
            recurrence_pattern='* * * * *'
        )
        self._experiment.delete()

        url = reverse('trial-schedule-detail',
                      kwargs={'experiment_id': self._experiment.id,
                              'pk': trial_schedule.id})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = [response.data]
        self.assertEqual(len(response_data), 1)
        self.assertIn(TrialScheduleSerializer(trial_schedule).data,
                      response_data)


class TestTrialScheduleCreateAPI(KallistiTestSuite):
    def setUp(self):
        super(TestTrialScheduleCreateAPI, self).setUp()
        self._token = '123123123123123'

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)
        self._experiment = Experiment.create()

    def tearDown(self):
        self.client.credentials()
        super(TestTrialScheduleCreateAPI, self).tearDown()

    def test_create(self):
        data = {'recurrence_pattern': '* * * * *'}
        url = reverse('trial-schedule-list',
                      kwargs={'experiment_id': self._experiment.id})
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrialSchedule.objects.count(), 1)

    def test_create_with_invalid_details(self):
        data = {'recurrence_pattern': 'invalid-cron-pattern'}
        url = reverse('trial-schedule-list',
                      kwargs={'experiment_id': self._experiment.id})
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TrialSchedule.objects.count(), 0)

    def test_create_with_invalid_experiment_id(self):
        data = {'recurrence_pattern': '* * * * *'}
        url = reverse('trial-schedule-list',
                      kwargs={'experiment_id': 'non-existing-experiment-id'})
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_on_deleted_experiment(self):
        data = {'recurrence_pattern': '* * * * *'}
        url = reverse('trial-schedule-list',
                      kwargs={'experiment_id': self._experiment.id})
        self._experiment.delete()
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(TrialSchedule.objects.count(), 0)


class TestTrialScheduleDeleteAPI(KallistiTestSuite):
    def setUp(self):
        super(TestTrialScheduleDeleteAPI, self).setUp()
        self._token = '123123123123123'
        self._non_existing_id = uuid4()
        self._non_existing_pk = uuid4()        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)

    def tearDown(self):
        self.client.credentials()
        super(TestTrialScheduleDeleteAPI, self).tearDown()

    def test_delete(self):
        experiment = Experiment.create()
        trial_schedule = TrialSchedule.create(experiment=experiment,
                                              recurrence_pattern='* * * * *')

        url = reverse('trial-schedule-detail',
                      kwargs={'experiment_id': experiment.id,
                              'pk': trial_schedule.id})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrialSchedule.objects.count(), 0)

    def test_delete_with_invalid_id(self):
        url = reverse('trial-schedule-detail',
                      kwargs={'experiment_id': self._non_existing_id,
                              'pk': self._non_existing_pk})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})


class TestTrialSchedulePatchAPI(KallistiTestSuite):
    def setUp(self):
        super(TestTrialSchedulePatchAPI, self).setUp()
        self._token = '123123123123123'
        self._non_existing_id = uuid4()
        self._non_existing_pk = uuid4()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._token)
        self._data = {'recurrence_pattern': '5 * * * *'}

    def tearDown(self):
        self.client.credentials()
        super(TestTrialSchedulePatchAPI, self).tearDown()

    def test_patch_with_invalid_id(self):
        url = reverse('trial-schedule-detail',
                      kwargs={'experiment_id': self._non_existing_id,
                              'pk': self._non_existing_pk})
        response = self.client.patch(url, data=self._data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

    def test_patch(self):
        experiment = Experiment.create()
        trial_schedule = TrialSchedule.create(experiment=experiment,
                                              recurrence_pattern='* * * * *')

        url = reverse('trial-schedule-detail',
                      kwargs={'experiment_id': experiment.id,
                              'pk': trial_schedule.id})
        response = self.client.patch(url, data=self._data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrialSchedule.objects.count(), 1)
        self.assertEqual('5 * * * *', response.data['recurrence_pattern'])
