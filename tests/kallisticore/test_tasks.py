from unittest import mock
from unittest.mock import Mock

from django.conf import settings
from django.test import TestCase

from kallisticore.models import Trial
from kallisticore.tasks import _execute_trial, _schedule_trials, \
    execute_trial, schedule_trials


class TestExecuteTrialTask(TestCase):

    @mock.patch("kallisticore.tasks._execute_trial")
    def test_execute_trial_task(self, method_mock):
        mock_trial = Mock(spec=Trial)
        execute_trial.func(mock_trial)

        method_mock.assert_called_once_with(mock_trial)

    @mock.patch("kallisticore.lib.trial_executor.TrialExecutor", autospec=True)
    def test_trial_executor_invoked(self, mock_trial_executor):
        mock_object = self.create_mock_trial_executor(mock_trial_executor)
        trial = {}

        _execute_trial(trial)

        self.assert_executor_called(mock_object, mock_trial_executor, trial)

    def assert_executor_called(self, mock_object, mock_trial_executor, trial):
        module_map = getattr(settings, 'KALLISTI_MODULE_MAP', {})
        cred_cls_map = getattr(settings, 'KALLISTI_CREDENTIAL_CLASS_MAP', {})
        mock_trial_executor.assert_called_once_with(trial, module_map,
                                                    cred_cls_map)

        mock_object.__enter__.assert_called_once()
        mock_object.__enter__.assert_called_once()
        mock_object.run.assert_called_once()
        mock_object.__exit__.assert_called_once()

    def create_mock_trial_executor(self, mock_trial_executor):
        mock_object = Mock()
        mock_object.__enter__ = Mock(return_value=mock_object)
        mock_object.__exit__ = Mock()
        mock_trial_executor.return_value = mock_object
        return mock_object


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
