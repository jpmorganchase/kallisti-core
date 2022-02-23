import datetime
from unittest import mock
from unittest.mock import Mock

from django.test import TestCase
from kallisticore.lib.trial_scheduler import schedule, _get_current_datetime
from kallisticore.models import Experiment, Trial


class TestTrialScheduler(TestCase):

    @mock.patch('kallisticore.lib.trial_scheduler.Trial')
    @mock.patch('kallisticore.lib.trial_scheduler._get_current_datetime')
    @mock.patch('kallisticore.lib.trial_scheduler.TrialSchedule')
    def test_schedule(self, mock_trial_schedule_class, mock_current_datetime,
                      mock_trial_class):
        mock_experiment = Experiment()
        mock_parameters = {'mock_param': 'mock-param-value'}
        mock_ticket = {'mock_ticket': 'mock-ticket-value'}
        mock_metadata = {'mock_metadata': 'mock-metadata-value'}
        mock_trials = Mock()

        mock_trial_schedule = Mock()
        mock_trial_schedule.experiment = mock_experiment
        mock_trial_schedule.recurrence_pattern = '* * * * *'
        mock_trial_schedule.ticket = mock_ticket
        mock_trial_schedule.parameters = mock_parameters
        mock_trial_schedule.metadata = mock_metadata
        mock_trial_schedule.trials = mock_trials

        class MockQuerySet:
            @staticmethod
            def all():
                return [mock_trial_schedule]

        class MockTrialObjects:
            @staticmethod
            def get_queryset():
                return MockQuerySet()

        mock_trial_schedule_class.objects = MockTrialObjects()
        mock_current_datetime.return_value = datetime.datetime(
            2019, 1, 1, 0, 0, 0)

        mock_trial_object = Trial()
        mock_trial_class.create.return_value = mock_trial_object

        mock_trial_schedule.should_execute_at.return_value = False
        schedule(60)
        mock_trial_class.create.assert_not_called()
        mock_trial_schedule.decrement_recurrence_left.assert_not_called()
        mock_trials.add.assert_not_called()

        mock_trial_schedule.should_execute_at.return_value = True
        schedule(60)

        mock_trial_class.create.assert_called_once_with(
            experiment=mock_experiment, parameters=mock_parameters,
            ticket=mock_ticket, metadata=mock_metadata)
        mock_trial_schedule.decrement_recurrence_left.assert_called_once()
        mock_trials.add.assert_called_once_with(mock_trial_object)

    def test_get_current_datetime(self):
        self.assertIsInstance(_get_current_datetime(), datetime.datetime)
