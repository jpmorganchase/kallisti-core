import errno

from unittest import mock

from kallisticore.utils.pid_manager import PidManager
from django.test import TestCase


class TestPid(TestCase):

    def test_validate_no_path(self):
        pid_manager = PidManager(None)
        self.assertTrue(pid_manager.validate())

    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_validate_no_file(self, _open):
        pid_manager = PidManager('test.pid')
        _open.side_effect = IOError(errno.ENOENT)
        self.assertTrue(pid_manager.validate())

    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_validate_other_io_error(self, _open):
        pid_manager = PidManager('test.pid')
        _open.side_effect = IOError(errno.EIO)
        with self.assertRaises(IOError) as err_context:
            pid_manager.validate()
            self.assertEqual(err_context.exception.args[0], errno.EIO)

    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='1')
    @mock.patch('os.kill')
    def test_validate_file_pid_exists(self, kill, _open):
        pid_manager = PidManager('test.pid')
        with self.assertRaises(RuntimeError) as err_context:
            pid_manager.validate()
            self.assertEqual(
                str(err_context.exception),
                'Already running on PID 1 (or pid file \'test.pid\' is stale)')
        self.assertTrue(kill.called)

    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='a')
    def test_validate_file_pid_malformed(self, _open):
        pid_manager = PidManager('test.pid')
        self.assertTrue(pid_manager.validate())

    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='1')
    @mock.patch('os.kill')
    def test_validate_file_pid_exists_kill_perm_exception(self, kill, _open):
        pid_manager = PidManager('test.pid')
        kill.side_effect = OSError(errno.EPERM)
        with self.assertRaises(RuntimeError) as err_context:
            pid_manager.validate()
            self.assertEqual(
                str(err_context.exception),
                'Already running on PID 1 (or pid file \'test.pid\' is stale)')

    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='1')
    @mock.patch('os.kill')
    def test_validate_file_pid_does_not_exist(self, kill, _open):
        pid_manager = PidManager('test.pid')
        kill.side_effect = OSError(errno.ESRCH)
        self.assertTrue(pid_manager.validate())

    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='1')
    @mock.patch('os.kill')
    def test_validate_file_pid_exists_kill_other_exception(self, kill, _open):
        pid_manager = PidManager('test.pid')
        kill.side_effect = OSError(errno.EBUSY)
        with self.assertRaises(OSError) as err_context:
            pid_manager.validate()
            self.assertEqual(err_context.exception.args[0], errno.EBUSY)
