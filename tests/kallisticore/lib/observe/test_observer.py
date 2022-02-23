import unittest
from typing import Any

from kallisticore.lib.observe.observer import Observer


class TestObserver(unittest.TestCase):
    def test_abstract_methods_implemented(self):
        class ConcreteObserver(Observer):
            def update(self, **kwargs: Any):
                super(ConcreteObserver, self).update()
        observer = ConcreteObserver()
        observer.update()

    def test_abstract_methods_not_implemented(self):
        class ConcreteObserver(Observer):
            pass
        with self.assertRaises(TypeError) as error:
            ConcreteObserver()
        self.assertEqual(
            "Can't instantiate abstract class ConcreteObserver with abstract "
            "method update",
            str(error.exception))
