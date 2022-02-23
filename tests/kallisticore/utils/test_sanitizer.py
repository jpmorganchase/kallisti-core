from kallisticore.utils.sanitizer import Sanitizer
from unittest import TestCase
from tests.kallisticore.utils.fixture.trial_result_data import \
    sanitizer_real_example_test, sanitizer_real_example_test_expected, \
    sanitizer_theoretical_test, sanitizer_theoretical_test_expected


class TestSanitizer(TestCase):

    def test_clean_sensitive_data_string(self):
        test_string = 'test-string'
        self.assertEqual(test_string,
                         Sanitizer.clean_sensitive_data(test_string))

    def test_clean_sensitive_data_theoretical(self):
        self.assertEqual(
            sanitizer_theoretical_test_expected,
            Sanitizer.clean_sensitive_data(sanitizer_theoretical_test))

    def test_clean_sensitive_data_real_example(self):
        self.assertEqual(
            sanitizer_real_example_test_expected,
            Sanitizer.clean_sensitive_data(sanitizer_real_example_test))
