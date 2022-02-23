import abc
import re
from abc import abstractmethod
from copy import deepcopy
from typing import Any, Dict

from jsonpath_ng.ext import parse
from kallisticore.exceptions import InvalidExpectOperator, FailedExpectation, \
    KeyNotFoundException


class Expectation(metaclass=abc.ABCMeta):

    @classmethod
    def build(cls, expectation_specification: Dict) -> 'Expectation':
        data = deepcopy(expectation_specification)
        operator = data.get('operator', None)
        if operator == RegexExpectation.REGEX_OPERATOR_VALUE:
            expectation = RegexExpectation.build(data)
        elif operator in OperatorExpectation.OPERATOR_MAP.keys():
            expectation = OperatorExpectation.build(data)
        else:
            raise InvalidExpectOperator(operator)
        return expectation

    @abstractmethod
    def execute(self, action_result):
        raise NotImplementedError


class OperatorExpectation(Expectation):
    OPERATOR_MAP = {
        'ne': '!=',
        'eq': '==',
        'le': '<=',
        'lt': '<',
        'ge': '>=',
        'gt': '>',
    }

    @classmethod
    def build(cls, data: Dict) -> 'OperatorExpectation':
        operator_key = data.pop('operator')
        operator = cls.OPERATOR_MAP[operator_key]
        expected_key, expected_value = None, None
        for key in data:
            expected_key, expected_value = key, data[key]
        return OperatorExpectation(operator, expected_key, expected_value)

    def __init__(self, operator: str, expected_key: str,
                 expected_value: object):
        super().__init__()
        self.operator = operator
        self.expected_key = expected_key
        self.expected_value = expected_value

    def execute(self, action_result):
        actual_value = self._align_float_values(
            ValueExtractor(action_result, self.expected_key).extract())

        expression = "actual_value {} self.expected_value".format(
            self.operator)
        if not eval(expression):
            raise FailedExpectation("{}".format("{} {} {}".format(
                actual_value, self.operator, self.expected_value)))

    def _align_float_values(self, actual_value: Any):
        """
        Function to align float values when both values to compare are
         float-able as float values are often strings in JSON format.
          E.g. Prometheus API. Specifically JSON does not support special
          float values such as NaN, Inf, and -Inf.
        """
        actual_float_value = self._try_float_cast(actual_value)
        expected_float_value = self._try_float_cast(self.expected_value)
        if isinstance(actual_float_value, float) and \
                isinstance(expected_float_value, float):
            self.expected_value = expected_float_value
            return actual_float_value
        return actual_value

    def _try_float_cast(self, value: Any) -> Any:
        if isinstance(value, float):
            return value
        if isinstance(value, str):
            return self.cast_float_or_none(value)
        return value

    @staticmethod
    def cast_float_or_none(value: str) -> Any:
        try:
            return float(value)
        except ValueError:
            return None


class RegexExpectation(Expectation):
    REGEX_OPERATOR_VALUE = 'regex'

    @classmethod
    def build(cls, data: Dict) -> 'RegexExpectation':
        expected_key, expected_value = None, None
        data.pop('operator')
        for key in data:
            expected_key, expected_value = key, data[key]
        return RegexExpectation(expected_key, expected_value)

    def __init__(self, expected_key: str, expected_value: str):
        super().__init__()
        self.expected_key = expected_key
        self.expected_value = expected_value

    def execute(self, action_result):
        actual_value = ValueExtractor(action_result,
                                      self.expected_key).extract()
        if not re.search(r"{}".format(self.expected_value), actual_value):
            raise FailedExpectation("Regex pattern {} does not match {}."
                                    .format(self.expected_value, actual_value))


class ValueExtractor:

    def __init__(self, input_data: object, key_path: str) -> None:
        self._key_path = key_path
        self._input = input_data

    def extract(self) -> Any:
        if isinstance(self._input, dict):
            return self.extract_key_path_from_input_of_type_dict()
        elif isinstance(self._input, list):
            return self.extract_key_path_from_input_of_type_list()
        else:
            return self.extract_key_path_from_input_of_type_other_than_dict()

    def extract_key_path_from_input_of_type_dict(self):
        matches = parse("$.{}".format(self._key_path)).find(self._input)
        if len(matches) < 1:
            self._raise_key_not_found_exception()
        return matches[0].value

    def extract_key_path_from_input_of_type_list(self):
        matches = parse("${}".format(self._key_path)).find(self._input)
        if len(matches) < 1:
            self._raise_key_not_found_exception()
        return matches[0].value

    def extract_key_path_from_input_of_type_other_than_dict(self):
        if self._key_path == 'value':
            return self._input
        self._raise_key_not_found_exception()

    def _raise_key_not_found_exception(self):
        raise KeyNotFoundException("The key path {} is not found in {}"
                                   .format(self._key_path, self._input))
