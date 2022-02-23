from unittest import TestCase

from kallisticore.utils.singleton import Singleton


class ClassA(metaclass=Singleton):

    def __init__(self):
        pass


class ClassB(metaclass=Singleton):

    def __init__(self, a):
        self.a = a


class ClassC(metaclass=Singleton):

    def __init__(self, a, b):
        self.a = a
        self.b = b


class TestSingleton(TestCase):

    def test_no_argument(self):
        self.assertEqual(id(ClassA()), id(ClassA()))

    def test_single_argument(self):
        self.assertEqual(id(ClassB("url")), id(ClassB("url")))
        self.assertNotEqual(id(ClassB("name")), id(ClassB("url")))

    def test_with_only_args(self):
        self.assertEqual(id(ClassC(1, 2)), id(ClassC(1, 2)))
        self.assertNotEqual(id(ClassC(1, 2)), id(ClassC(3, 4)))

    def test_with_only_kwargs(self):
        self.assertEqual(id(ClassC(a=1, b=2)), id(ClassC(a=1, b=2)))
        self.assertNotEqual(id(ClassC(a=1, b=2)), id(ClassC(a=3, b=4)))

    def test_with_both_args_kwargs(self):
        self.assertEqual(id(ClassC(1, b=2)), id(ClassC(a=1, b=2)))
        self.assertEqual(id(ClassC(1, 2)), id(ClassC(a=1, b=2)))
        self.assertNotEqual(id(ClassC(1, b=2)), id(ClassC(a=3, b=4)))
