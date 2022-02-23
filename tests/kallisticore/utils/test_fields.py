import json

from django.test import TestCase
from kallisticore.models.step import Step
from kallisticore.utils.fields import DictField, ListField, ValidationError, \
    StepsField


class TestListField(TestCase):
    def setUp(self):
        self._list = ['a', 'b']
        self._json_input = json.dumps(self._list)

    """
    Tests for method from_db_value
    """

    def test_from_db_value(self):
        field = ListField().from_db_value(self._json_input)

        self.assertEqual(2, len(field))
        self.assertEqual(self._list[0], field[0])
        self.assertEqual(self._list[1], field[1])

    def test_from_db_value_with_None(self):
        field = ListField().from_db_value(None)

        self.assertEqual(0, len(field))

    def test_from_db_value_with_empty_str(self):
        field = ListField().from_db_value("")

        self.assertEqual(0, len(field))

    def test_from_db_value_with_invalid_field(self):
        with self.assertRaises(ValidationError) as error:
            ListField().from_db_value("[")

        self.assertEqual(error.exception.message,
                         "Invalid format: Expecting value")

    """
    Tests for method to_python
    """

    def test_to_python_for_valid_list(self):
        field = ListField().to_python(self._json_input)

        self.assertEqual(2, len(field))
        self.assertEqual(self._list[0], field[0])
        self.assertEqual(self._list[1], field[1])

    def test_to_python_with_None(self):
        field = ListField().to_python(None)

        self.assertEqual(0, len(field))

    def test_to_python_with_empty_str(self):
        field = ListField().to_python("")

        self.assertEqual(0, len(field))

    def test_to_python_with_python_list(self):
        field = ListField().to_python(self._list)

        self.assertEqual(2, len(field))
        self.assertEqual(self._list[0], field[0])
        self.assertEqual(self._list[1], field[1])

    """
    Tests for method get_prep_value
    """

    def test_get_prep_value_with_list(self):
        value = ListField().get_prep_value(self._list)

        self.assertEqual(self._json_input, value)

    def test_get_prep_value_with_json(self):
        value = ListField().get_prep_value(self._json_input)
        self.assertEqual(self._json_input, value)


class TestStepsField(TestCase):
    def setUp(self):
        self._step1 = {
            "do": "cm.http_health_check",
            "where": {"url": "https://app.test"}
        }

        self._step2 = {
            "do": "cm.wait",
            "where": {"time_in_seconds": 2}
        }

    """
    Tests for method from_db_value
    """

    def test_from_db_value_with_valid_step_list(self):
        steps = StepsField().from_db_value('[' + json.dumps(self._step1) + ']')

        self.assertEqual(1, len(steps))
        step1 = steps[0]
        self.assertIsInstance(step1, Step)
        self.assertEqual(Step.build(self._step1), step1)

    def test_from_db_value_with_none(self):
        steps = StepsField().from_db_value(None)

        self.assertEqual(0, len(steps))

    def test_from_db_value_with_empty_str(self):
        steps = StepsField().from_db_value("")

        self.assertEqual(0, len(steps))

    def test_from_db_value_with_invalid_value(self):
        with self.assertRaises(ValidationError) as error:
            StepsField().from_db_value("[")

        self.assertEqual(error.exception.message,
                         "Invalid format: Expecting value")

    def test_from_db_value_with_invalid_step(self):
        invalid_step = {"do": "cm.wait"}
        invalid_step_json = json.dumps(invalid_step)

        with self.assertRaises(ValidationError) as error:
            StepsField().from_db_value("[" + invalid_step_json + "]")

        self.assertEqual(
            "Invalid Steps: Some steps provided are invalid. "
            "Invalid Steps: [" + invalid_step_json + "]",
            error.exception.message)

    """
    Tests for method to_python
    """

    def test_to_python_with_valid_step_list(self):
        steps = StepsField().to_python(json.dumps([self._step1]))

        self.assertEqual(1, len(steps))
        step1 = steps[0]
        self.assertIsInstance(step1, Step)
        self.assertEqual(Step.build(self._step1), step1)

    def test_to_python_with_none(self):
        steps = StepsField().to_python(None)

        self.assertEqual(0, len(steps))

    def test_to_python_with_empty_str(self):
        steps = StepsField().to_python("")

        self.assertEqual(0, len(steps))

    def test_to_python_with_step_list(self):
        steps = StepsField().to_python([self._step1])

        self.assertEqual(1, len(steps))
        self.assertIsInstance(steps[0], Step)
        self.assertEqual(steps[0], Step.build(self._step1))

    """
    Tests for method get_prep_value
    """

    def test_get_prep_value_with_step_list(self):
        value = StepsField().get_prep_value([Step.build(self._step1)])
        self.assertEqual(json.dumps([self._step1]), value)

    def test_get_prep_value_with_json_string(self):
        value = StepsField().get_prep_value(
            '[' + json.dumps(self._step1) + ']')
        self.assertEqual([self._step1], json.loads(value))


class TestDictField(TestCase):
    def setUp(self):
        self._parameters = {"instances_to_kill": 1, "app_name": "my-app",
                            "org": "my-org", "key1": "value1",
                            "key2": "value2"}

        """
        Tests for method from_db_value
        """

    def test_from_db_value_with_valid_param(self):
        parameters = DictField().from_db_value(json.dumps(self._parameters))

        self.assertEqual(5, len(parameters))
        self.assertIsInstance(parameters, dict)
        self.assertEqual(parameters, self._parameters)

    def test_from_db_value_with_none(self):
        parameters = DictField().from_db_value(None)

        self.assertEqual(0, len(parameters))

    def test_from_db_value_with_empty_str(self):
        parameters = DictField().from_db_value("")

        self.assertEqual(0, len(parameters))

    def test_from_db_value_with_invalid_value(self):
        with self.assertRaises(ValidationError) as error:
            DictField().from_db_value("[")

        self.assertEqual(error.exception.message,
                         "Invalid format: Expecting value")

    """
    Tests for method to_python
    """

    def test_to_python_valid_json(self):
        parameters = DictField().to_python(json.dumps(self._parameters))

        self.assertEqual(5, len(parameters))
        self.assertIsInstance(parameters, dict)

        self.assertEqual(parameters, self._parameters)

    def test_to_python_with_none(self):
        parameters = DictField().to_python(None)

        self.assertEqual(0, len(parameters))

    def test_to_python_with_empty_str(self):
        parameters = DictField().to_python("")

        self.assertEqual(0, len(parameters))

    def test_to_python_with_dict(self):
        parameters = DictField().to_python(self._parameters)

        self.assertEqual(5, len(parameters))
        self.assertIsInstance(parameters, dict)
        self.assertEqual(parameters, self._parameters)

    """
    Tests for method get_prep_value
    """

    def test_get_prep_value_with_dict(self):
        value = DictField().get_prep_value(self._parameters)
        self.assertEqual(json.dumps(self._parameters), value)

    def test_get_prep_value_with_json_string(self):
        value = DictField().get_prep_value(json.dumps(self._parameters))
        self.assertEqual(self._parameters, json.loads(value))
