import json
import os
import sys
from logging import LogRecord
from unittest import mock

from django.test import TestCase

from kallisticore.utils.logging import KallistiLogStashFormatter


class TestLogging(TestCase):
    def setUp(self):
        self.formatter = KallistiLogStashFormatter()

    def test_formatter_normal(self):
        log_record = LogRecord(name='django.server', level='TEST_WARN',
                               pathname='TEST_PATH_NAME',
                               lineno='TEST_LINE_NO', msg='%s',
                               args=('POST /api/v1/experiment HTTP/1.1',),
                               exc_info=None)
        result = json.loads(self.formatter.format(log_record))
        self.assertEqual(result['logger_name'], log_record.name)
        self.assertEqual(result['message'], log_record.getMessage())
        self.assertEqual(result['level'], log_record.levelname)
        self.assertEqual(result['type'], 'POST')
        self.assertEqual(result['path'], '/api/v1/experiment')

    @mock.patch("kallisticore.utils.threadlocals.ThreadLocal.get_attr")
    def test_formatter_user_id_in_local_thread(self, mock_user_id_getter):
        mock_user_id_getter.return_value = "X112233"

        log_record = LogRecord(name='django.server', level='TEST_WARN',
                               pathname='TEST_PATH_NAME',
                               lineno='TEST_LINE_NO', msg='%s',
                               args=('POST /api/v1/experiment HTTP/1.1',),
                               exc_info=None)
        result = json.loads(self.formatter.format(log_record))

        self.assertEqual(result['logger_name'], log_record.name)
        self.assertEqual(result['message'], log_record.getMessage())
        self.assertEqual(result['level'], log_record.levelname)
        self.assertEqual(result['type'], 'POST')
        self.assertEqual(result['path'], '/api/v1/experiment')
        self.assertEqual(result['user_id'], "X112233")

        mock_user_id_getter.assert_called_once_with("user_id", None)

    def test_formatter_exception(self):
        log_record = LogRecord(name='django.server', level='TEST_WARN',
                               pathname='TEST_PATH_NAME',
                               lineno='TEST_LINE_NO', msg='%s',
                               args=('POST /api/v1/experiment HTTP/1.1',),
                               exc_info=sys.exc_info())
        result = json.loads(self.formatter.format(log_record))
        # these fields should be exist.
        self.assertTrue('stack_trace' in result)
        self.assertTrue('thread_name' in result)
        self.assertTrue('stack_info' in result)
        self.assertEqual(result['process'], os.getpid())
