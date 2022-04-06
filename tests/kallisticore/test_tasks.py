from unittest import mock
from unittest.mock import Mock

from django.test import TestCase

from kallisticore.models import Trial
from kallisticore.tasks import _schedule_trials, \
    execute_trial, schedule_trials


class TestExecuteTrialTask(TestCase):

    @mock.patch("kallisticore.tasks.exec_trial")
    def test_execute_trial_task(self, method_mock):
        mock_trial = Mock(spec=Trial)
        execute_trial.func(mock_trial)

        method_mock.assert_called_once_with(mock_trial)


class TestScheduleTrialTask(TestCase):

    @mock.patch("kallisticore.tasks._schedule_trials")
    def test_schedule_trials_task(self, method_mock):
        schedule_trials.func()

        method_mock.assert_called_once_with(60)

    @mock.patch('kallisticore.tasks.schedule')
    def test_trial_schedule_is_invoked(self, mock_trial_schedule):
        interval_seconds = 55
        _schedule_trials(interval_seconds)
        mock_trial_schedule.assert_called_with(interval_seconds)
