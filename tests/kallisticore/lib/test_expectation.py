from unittest import TestCase
from unittest.mock import patch

from kallisticore.exceptions import InvalidExpectOperator, FailedExpectation, \
    KeyNotFoundException
from kallisticore.lib.expectation import Expectation, OperatorExpectation, \
    RegexExpectation, ValueExtractor


class TestExpectation(TestCase):
    def test_build_arithmetic_operator_expectation(self):
        expect_spec = {"operator": "eq", "value": 2}
        self.assertIsInstance(Expectation.build(expect_spec),
                              OperatorExpectation)

    def test_build_regex_expectation(self):
        expect_spec = {"operator": "regex", "status_text": "/Hello/"}
        self.assertIsInstance(Expectation.build(expect_spec), RegexExpectation)

    def test_build_throws_an_error_when_operator_is_invalid(self):
        expect_spec = {"operator": "invalid-operator",
                       "status_text": "/Hello/"}
        with self.assertRaises(InvalidExpectOperator) as error:
            Expectation.build(expect_spec)
        self.assertEqual("Invalid operator: invalid-operator",
                         error.exception.message)

    def test_build_throws_an_error_when_operator_is_not_provided(self):
        expect_spec = {"status_text": "/Hello/"}
        with self.assertRaises(InvalidExpectOperator) as error:
            Expectation.build(expect_spec)
        self.assertEqual("Invalid operator: None", error.exception.message)

    @patch.multiple(Expectation, __abstractmethods__=set())
    def test_execute(self):
        result = "mock-result"
        with self.assertRaises(NotImplementedError):
            Expectation().execute(result)


class TestArithmeticExpectation(TestCase):
    # Operator eq

    def test_passes_for_integer_values(self):
        integer_test_cases = [
            {
                'expect_spec': {"operator": "ne", "value": 2},
                'input': 3
            },
            {
                'expect_spec': {"operator": "eq", "value": 2},
                'input': 2
            },
            {
                'expect_spec': {"operator": "lt", "value": 3},
                'input': 2
            },
            {
                'expect_spec': {"operator": "le", "value": 2},
                'input': 1
            },
            {
                'expect_spec': {"operator": "le", "value": 2},
                'input': 2
            },
            {
                'expect_spec': {"operator": "gt", "value": 2},
                'input': 3
            },
            {
                'expect_spec': {"operator": "ge", "value": 2},
                'input': 2
            },
            {
                'expect_spec': {"operator": "ge", "value": 2},
                'input': 3
            },
            {
                'expect_spec': {"operator": "ge", "value": "2.0"},
                'input': "3.0"
            },
            {
                'expect_spec': {"operator": "ge", "value": 2.0},
                'input': "3.0"
            },
            {
                'expect_spec': {"operator": "ge", "value": "2.0"},
                'input': 3.0
            },
        ]
        for test_cases in integer_test_cases:
            expect_spec = test_cases['expect_spec']
            input_value = test_cases['input']
            with self.subTest(operator=expect_spec['operator'],
                              expect_spec=expect_spec, input=input_value):
                expectation = OperatorExpectation.build(expect_spec)
                self.assertIsNone(expectation.execute(input_value))

    def test_passes_for_string_values(self):
        string_test_cases = [
            {
                'expect_spec': {"operator": "ne", "value": "bee"},
                'input': "honey"
            },
            {
                'expect_spec': {"operator": "eq", "value": "honey bee"},
                'input': "honey bee"
            }
        ]
        for test_cases in string_test_cases:
            expect_spec = test_cases['expect_spec']
            input_value = test_cases['input']
            with self.subTest(operator=expect_spec['operator'],
                              expect_spec=expect_spec, input=input_value):
                expectation = OperatorExpectation.build(expect_spec)

                self.assertIsNone(expectation.execute(input_value))

    def test_passes_for_boolean_values(self):
        string_test_cases = [
            {
                'expect_spec': {"operator": "ne", "value": True},
                'input': False
            },
            {
                'expect_spec': {"operator": "eq", "value": True},
                'input': True
            }
        ]
        for test_cases in string_test_cases:
            expect_spec = test_cases['expect_spec']
            input_value = test_cases['input']
            with self.subTest(operator=expect_spec['operator'],
                              expect_spec=expect_spec, input=input_value):
                expectation = OperatorExpectation.build(expect_spec)

                self.assertIsNone(expectation.execute(input_value))

    def test_passes_for_values_in_dict(self):
        dict_test_cases = [
            {
                'expect_spec': {"operator": "ne", "status_code": 500},
                'input': {'status_code': 200, 'response_text': 'UP'}
            },
            {
                'expect_spec': {"operator": "eq", "status_code": 200},
                'input': {'status_code': 200, 'response_text': 'UP'}
            },
            {
                'expect_spec': {"operator": "ne", "health.service_a": "DOWN"},
                'input': {'status_code': 200, 'response_text': 'UP',
                          'health': {'service_a': 'UP', 'service_b': 'UP'}}
            },
            {
                'expect_spec': {"operator": "eq", "health.service_a": "UP"},
                'input': {'status_code': 200, 'response_text': 'UP',
                          'health': {'service_a': 'UP', 'service_b': 'UP'}}
            }
        ]
        for test_cases in dict_test_cases:
            expect_spec = test_cases['expect_spec']
            input_value = test_cases['input']
            with self.subTest(operator=expect_spec['operator'],
                              expect_spec=expect_spec, input=input_value):
                expectation = OperatorExpectation.build(expect_spec)

                self.assertIsNone(expectation.execute(input_value))

    def test_raise_exception_when_expectation_fails(self):
        expect_spec = {"operator": "eq", "value": 3}
        expectation = Expectation.build(expect_spec)
        with self.assertRaises(FailedExpectation) as error:
            expectation.execute(2)

        self.assertEqual("Expectation failed(2 == 3)", str(error.exception))

    def test_raise_exception_for_dict_key_value_comparision(self):
        expect_spec = {"operator": "eq", "status_code": 500}
        expectation = Expectation.build(expect_spec)
        result = {'status_code': 200, 'response_text': 'UP'}
        with self.assertRaises(FailedExpectation) as error:
            expectation.execute(result)
        self.assertEqual("Expectation failed(200 == 500)",
                         str(error.exception))


class TestRegexExpectation(TestCase):
    def setUp(self):
        self.expect_spec = {"operator": "regex", "response_text": "UP"}
        self.expectation = RegexExpectation.build(self.expect_spec)

    def test_execute_for_regex_when_expect_passes(self):
        action_result = {'status_code': 200, 'response_text': 'UP'}

        self.assertIsNone(self.expectation.execute(action_result))

    def test_execute_for_regex_when_expect_fails(self):
        action_result = {'status_code': 200, 'response_text': 'DOWN'}

        with self.assertRaises(FailedExpectation) as error:
            self.expectation.execute(action_result)

        self.assertEqual("Expectation failed"
                         "(Regex pattern UP does not match DOWN.)",
                         str(error.exception))


class TestValueExtractor(TestCase):
    def test_initialize(self):
        data = {'a': "hello world"}
        key_path = 'a'
        extractor = ValueExtractor(data, key_path)

        self.assertEqual(data, extractor._input)
        self.assertEqual(key_path, extractor._key_path)

    def test_extract_with_value_from_integer_input(self):
        data = 1
        key_path = 'value'
        extractor = ValueExtractor(data, key_path)

        self.assertEqual(1, extractor.extract())

    def test_exception_with_non_value_from_integer_input(self):
        data = 1
        key_path = 'foobar'
        extractor = ValueExtractor(data, key_path)

        with self.assertRaises(KeyNotFoundException) as error:
            extractor.extract()

        self.assertEqual("The key path foobar is not found in 1",
                         error.exception.message)

    def test_extract_value_of_key_from_dict(self):
        data = {'a': "hello world"}
        key_path = 'a'
        extractor = ValueExtractor(data, key_path)

        self.assertEqual("hello world", extractor.extract())

    def test_extract_value_of_nested_key_from_dict(self):
        data = {'a': {'b': "hello world"}}
        key_path = 'a.b'
        extractor = ValueExtractor(data, key_path)

        self.assertEqual("hello world", extractor.extract())

    def test_raise_exception(self):
        data = {'a': {'b': "hello world"}}
        key_path = 'a.c'
        extractor = ValueExtractor(data, key_path)

        with self.assertRaises(KeyNotFoundException) as error:
            extractor.extract()

        self.assertEqual("The key path a.c is not found in "
                         "{'a': {'b': 'hello world'}}",
                         error.exception.message)

    def test_extract_value_from_array_with_index(self):
        data = [1, 2, 3]
        key_path = '[1]'
        extractor = ValueExtractor(data, key_path)

        self.assertEqual(2, extractor.extract())

    def test_extract_value_of_key_from_array_with_index(self):
        data = [{'name': 'a', 'value': 1}, {'name': 'b', 'value': 2}]
        key_path = '[1].value'
        extractor = ValueExtractor(data, key_path)

        self.assertEqual(2, extractor.extract())

    def test_extract_value_of_key_from_array_with_value_match(self):
        data = [{'name': 'a', 'value': 1}, {'name': 'b', 'value': 2}]
        key_path = '[?(@.name=="b")].value'
        extractor = ValueExtractor(data, key_path)

        self.assertEqual(2, extractor.extract())

    def test_raise_exception_when_index_is_not_found(self):
        data = [1, 2, 3]
        key_path = '[3]'
        extractor = ValueExtractor(data, key_path)

        with self.assertRaises(KeyNotFoundException) as error:
            extractor.extract()

        self.assertEqual("The key path [3] is not found in [1, 2, 3]",
                         error.exception.message)
