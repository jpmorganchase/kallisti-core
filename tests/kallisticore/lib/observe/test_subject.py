import unittest
from unittest.mock import Mock

from kallisticore.lib.observe.observer import Observer
from kallisticore.lib.observe.subject import Subject


class TestSubject(unittest.TestCase):
    class ConcreteSubject(Subject):
        pass

    def setUp(self) -> None:
        self.mock_logger = Mock()
        self.sub = self.ConcreteSubject()
        self.sub.logger = self.mock_logger

    def test_initialize(self):
        self.assertEqual([], self.sub._observers)

    def test_attach(self):
        observer = Mock(spec=Observer)

        self.sub.attach(observer)

        self.assertEqual([observer], self.sub._observers)

    def test_detach(self):
        observer = Mock(spec=Observer)
        self.sub._observers = [observer]

        self.sub.detach(observer)

        self.assertEqual([], self.sub._observers)

    def test_notify(self):

        observer = Mock(spec=Observer)
        self.sub._observers = [observer]

        self.sub.notify()

        observer.update.assert_called_once_with()

    def test_notify_should_pass_the_kwargs_to_observer(self):
        observer = Mock(spec=Observer)
        self.sub._observers = [observer]

        self.sub.notify(key='value')

        observer.update.assert_called_once_with(key='value')

    def test_notify_should_call_all_observers_despite_failures(self):
        observer1 = Mock(spec=Observer)
        observer1.update.side_effect = Exception('something went wrong')
        observer2 = Mock(spec=Observer)
        self.sub._observers = [observer1, observer2]

        self.sub.notify()

        observer1.update.assert_called_once_with()
        observer2.update.assert_called_once_with()
        self.mock_logger.error.assert_called_once_with("something went wrong")
