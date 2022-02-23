import datetime
import json
import time
from collections import OrderedDict
from unittest import mock

from django.test import TestCase
from kallisticore.lib.trial_log_recorder import TrialLogRecord, \
    TrialStepLogRecord, TrialLogRecorder


class TestTrialLogRecorder(TestCase):
    def setUp(self):
        self.trial_id = 'test-trial-id'
        self.trial_log_recorder = TrialLogRecorder(self.trial_id)

    def test_trial_log_recorder_init(self):
        self.assertEqual(self.trial_log_recorder.trial_id, self.trial_id)
        self.assertEqual(self.trial_log_recorder.trial_record, {})

    def test_trial_log_append(self):
        timestamp = time.time()
        timestamp_string = datetime.datetime.fromtimestamp(timestamp).strftime(
            '%Y-%m-%dT%H:%M:%SZ')
        with mock.patch('time.time') as mock_time:
            mock_time.return_value = timestamp
            level = 'INFO'
            message = 'Test message'

            trial_log = TrialLogRecord('steps')
            trial_log.append(level, message)

            self.assertEqual(trial_log.logs, [
                '[{} - {}] {}'.format(timestamp_string, level, message)
            ])

    def test_trial_log_recorder_append_multiple_logs(self):
        timestamp = time.time()
        timestamp_string = datetime.datetime.fromtimestamp(timestamp).strftime(
            '%Y-%m-%dT%H:%M:%SZ')

        with mock.patch('time.time') as mock_time:
            mock_time.return_value = timestamp
            level = 'INFO'
            message = 'Test message'
            trial_stage = 'steps'

            trial_log = TrialLogRecord(trial_stage)
            trial_log.append(level, message)
            trial_log.append(level, message)

            self.assertEqual(trial_log.trial_stage, trial_stage)
            self.assertEqual(trial_log.logs, [
                '[{} - {}] {}'.format(timestamp_string, level, message),
                '[{} - {}] {}'.format(timestamp_string, level, message)
            ])

    def test_trial_log_recorder_make(self):
        timestamp = time.time()
        timestamp_string = datetime.datetime.fromtimestamp(timestamp).strftime(
            '%Y-%m-%dT%H:%M:%SZ')

        with mock.patch('time.time') as mock_time:
            mock_time.return_value = timestamp
            level = 'INFO'
            message = 'Test message'
            trial_stage = 'steps'

            trial_log = TrialLogRecord(trial_stage)
            trial_log.append(level, message)
            trial_log.append(level, message)

            self.assertEqual(trial_log.trial_stage, trial_stage)
            self.assertEqual(trial_log.make(), OrderedDict(
                [
                    ('logs',
                     ['[{} - INFO] Test message'.format(timestamp_string),
                      '[{} - INFO] Test message'.format(timestamp_string)])
                ]
            ))

    def test_trial_step_log_recorder_make(self):
        timestamp = time.time()
        timestamp_string = datetime.datetime.fromtimestamp(timestamp).strftime(
            '%Y-%m-%dT%H:%M:%SZ')

        with mock.patch('time.time') as mock_time:
            mock_time.return_value = timestamp
            level = 'INFO'
            message = 'Test message'
            trial_stage = 'steps'

            trial_log = TrialStepLogRecord(trial_stage, 'test name',
                                           {'key': 'value'})
            trial_log.append(level, message)
            trial_log.append(level, message)

            self.assertEqual(trial_log.trial_stage, trial_stage)
            self.assertEqual(trial_log.make(), OrderedDict(
                [
                    ('step_name', 'test name'),
                    ('step_parameters', {'key': 'value'}),
                    ('logs',
                     ['[{} - INFO] Test message'.format(timestamp_string),
                      '[{} - INFO] Test message'.format(timestamp_string)])
                ]
            ))

    def test_trial_log_recorder_commit_logs(self):
        timestamp = time.time()
        timestamp_string = datetime.datetime.fromtimestamp(timestamp).strftime(
            '%Y-%m-%dT%H:%M:%SZ')

        with mock.patch('time.time') as mock_time, \
                mock.patch('kallisticore.models.trial.Trial.objects.filter')\
                as mock_trial_object_filter:
            mock_filter = mock.Mock()
            mock_filter.update = mock.Mock()
            mock_trial_object_filter.return_value = mock_filter
            mock_time.return_value = timestamp
            level = 'INFO'
            message = 'Test message'
            trial_stage = 'steps'

            trial_log = TrialLogRecord(trial_stage)
            trial_log.append(level, message)
            trial_log.append(level, message)
            self.trial_log_recorder.commit(trial_log)

            # trial_record shouldnt be reset after commit
            self.assertEqual({trial_stage: [OrderedDict(
                [('logs', ['[{} - INFO] Test message'.format(timestamp_string),
                           '[{} - INFO] Test message'.format(
                               timestamp_string)])]
            )]}, self.trial_log_recorder.trial_record)
            self.assertEqual(trial_log.trial_stage, trial_stage)
            mock_trial_object_filter.assert_called_once_with(pk=self.trial_id)
            mock_filter.update.assert_called_once_with(
                records=json.dumps(self.trial_log_recorder.trial_record))

    def test_trial_log_recorder_commit_trial_step_logs(self):
        timestamp = time.time()
        timestamp_string = datetime.datetime.fromtimestamp(timestamp).strftime(
            '%Y-%m-%dT%H:%M:%SZ')

        with mock.patch('time.time') as mock_time, \
                mock.patch('kallisticore.models.trial.Trial.objects.filter')\
                as mock_trial_object_filter:
            mock_filter = mock.Mock()
            mock_filter.update = mock.Mock()
            mock_trial_object_filter.return_value = mock_filter
            mock_time.return_value = timestamp
            level = 'INFO'
            message = 'Test message'
            trial_stage = 'steps'

            trial_log = TrialStepLogRecord(trial_stage, 'test-step',
                                           {'key': 'value'})
            trial_log.append(level, message)
            self.trial_log_recorder.commit(trial_log)

            # trial_record shouldnt be reset after commit
            self.assertEqual({trial_stage: [OrderedDict(
                [
                    ('step_name', 'test-step'),
                    ('step_parameters', {'key': 'value'}),
                    ('logs',
                     ['[{} - INFO] Test message'.format(timestamp_string)])
                ]
            )]}, self.trial_log_recorder.trial_record)
            mock_trial_object_filter.assert_called_once_with(pk=self.trial_id)
            mock_filter.update.assert_called_once_with(
                records=json.dumps(self.trial_log_recorder.trial_record))

    def test_trial_log_recorder_commit_logs_exception(self):
        with mock.patch('kallisticore.models.trial.Trial.objects.filter')\
            as mock_trial_object_filter, mock.patch(
            'kallisticore.lib.trial_log_recorder.TrialLogRecorder.'
                'logger.warning') as mock_logger:
            expected_exception = Exception('test error')
            mock_trial_object_filter.side_effect = Exception('test error')
            level = 'INFO'
            message = 'Test message'
            trial_stage = 'steps'

            trial_log = TrialLogRecord(trial_stage)
            trial_log.append(level, message)
            trial_log.append(level, message)
            self.trial_log_recorder.commit(trial_log)

            self.assertEqual(trial_log.trial_stage, trial_stage)
            mock_logger.assert_called_once_with(
                "Failed to update 'records' column for trial {}, {}"
                .format(self.trial_id, expected_exception))
