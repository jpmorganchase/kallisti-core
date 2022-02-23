from django.test import TestCase

from kallisticore.models.step import Step


class TestStep(TestCase):
    def setUp(self):
        self.desc = "description"
        self.action = "cf.get_org_by_name"
        self.where_clause = {"cf_api_url": "https://cf.test"}
        self.expect_clause = [{"operator": "eq", "value": "TEST_ORG"}]
        self.steps_dict = {"step": self.desc,
                           "do": self.action,
                           "where": self.where_clause,
                           "expect": self.expect_clause}

    def test_build(self):
        step = Step.build(self.steps_dict)

        self.assertEqual(self.desc, step.description)
        self.assertEqual(self.action, step.action)
        self.assertEqual(self.where_clause, step.where)
        self.assertEqual(self.expect_clause, step.expect)

    def test_build_when_no_expect_list_is_provided(self):
        step = Step.build(
            {"do": self.action, "step": self.desc, "where": self.where_clause})

        self.assertEqual(self.desc, step.description)
        self.assertEqual(self.action, step.action)
        self.assertEqual(self.where_clause, step.where)
        self.assertEqual([], step.expect)

    def test_build_when_no_description_is_provided(self):
        step = Step.build({"do": self.action, "where": self.where_clause})

        self.assertEqual(None, step.description)
        self.assertEqual(self.action, step.action)
        self.assertEqual(self.where_clause, step.where)

    def test_initialize(self):
        where_clause = {"url": "http://app.test"}
        step = Step("cm.http_health_check", "description text", where_clause)

        self.assertEqual("description text", step.description)
        self.assertEqual("cm.http_health_check", step.action)
        self.assertEqual(where_clause, step.where)

    def test_is_valid_for_valid_step(self):
        step = Step(self.action, self.desc, self.where_clause)
        self.assertEqual(True, step.is_valid())

    def test_is_valid_returns_false_when_action_not_present(self):
        step = Step(None, self.desc, self.where_clause)
        self.assertEqual(False, step.is_valid())

    def test_is_valid_returns_false_when_where_not_present(self):
        step = Step(self.action, self.desc, None)
        self.assertEqual(False, step.is_valid())

    def test_get_namespace(self):
        step = Step.build(self.steps_dict)
        self.assertEqual("cf", step.get_namespace())

    def test_get_function_name(self):
        step = Step.build(self.steps_dict)
        self.assertEqual("get_org_by_name", step.get_function_name())

    def test_to_dict(self):
        step = Step.build(self.steps_dict)
        self.assertEqual(self.steps_dict, step.to_dict())

    def test_to_dict_when_description_not_present(self):
        step_dict = {"do": "test", "where": {"a": "b"}}
        step = Step.build(step_dict)
        self.assertEqual(step_dict, step.to_dict())

    def test_encode(self):
        step = Step.build(self.steps_dict)
        self.assertEqual(self.steps_dict, Step.encode_step(step))

    def test_encode_when_description_not_present(self):
        step_dict = {"do": "test", "where": {"a": "b"}}
        step = Step.build(step_dict)
        self.assertEqual(step_dict, Step.encode_step(step))

    def test_encode_invalid_step(self):
        with self.assertRaises(TypeError) as error:
            Step.encode_step("invalid")

        self.assertEqual(
            "Object of type 'str' is not JSON serializable "
            "using Step.encode_step",
            str(error.exception))

    def test_items_return_list_of_tuples_in_expected_order(self):
        # Order of keys: "step", "do", "where
        step = Step.build(self.steps_dict)
        self.assertEqual(
            [(Step.DESC_KEY, step.description), (Step.ACTION_KEY, step.action),
             (Step.WHERE_KEY, step.where)],
            step.items())

    def test_items_return_list_of_tuples_in_expected_order_no_description(
            self):
        # Order of keys: "step", "do", "where
        step = Step.build({"do": "test", "where": {"a": "b"}})
        self.assertEqual(
            [(Step.ACTION_KEY, step.action), (Step.WHERE_KEY, step.where)],
            step.items())

    def test_interpolate_with_parameters(self):
        app_health_endpoint = "http://myapp.test/health"
        step = Step(action="cm.http_health_check", description='',
                    where={"url": "{{ app_health_endpoint }}"})

        step.interpolate_with_parameters(
            {"app_health_endpoint": app_health_endpoint})

        self.assertEqual({"url": app_health_endpoint}, step.where)
