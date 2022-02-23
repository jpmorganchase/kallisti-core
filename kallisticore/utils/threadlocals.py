from threading import local


class ThreadLocal:
    _thread_local = local()

    @staticmethod
    def set_attr(key, value):
        setattr(ThreadLocal._thread_local, key, value)

    @staticmethod
    def get_attr(key, default=None):
        return getattr(ThreadLocal._thread_local, key, default)
