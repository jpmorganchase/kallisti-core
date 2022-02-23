import errno
import os


class PidManager(object):

    def __init__(self, file_name):
        self.file_name = file_name
        self.pid = None

    def validate(self) -> bool:
        if not self.file_name:
            return True
        try:
            old_pid = self._read_pid()
            try:
                os.kill(old_pid, 0)
                self._raise_already_running_error(old_pid)
            except OSError as e:
                if e.args[0] == errno.EPERM:
                    self._raise_already_running_error(old_pid)
                if e.args[0] == errno.ESRCH:
                    return True
                raise e
        except IOError as e:
            if e.args[0] == errno.ENOENT:
                return True
            raise e
        except ValueError:
            return True

    def _read_pid(self) -> int:
        with open(self.file_name, "r") as f:
            return int(f.read())

    def _raise_already_running_error(self, old_pid: int):
        msg = "Already running on PID %s (or pid file '%s' is stale)"
        raise RuntimeError(msg % (old_pid, self.file_name))
