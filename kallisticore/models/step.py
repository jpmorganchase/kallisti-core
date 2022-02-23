import json
from typing import Dict, List, Tuple

from django.core.exceptions import ValidationError
from jinja2 import Template, Environment, meta


class Step:
    ACTION_KEY = "do"
    DESC_KEY = "step"
    WHERE_KEY = "where"
    EXPECT_KEY = "expect"

    @classmethod
    def build(cls, step_dict: Dict) -> "Step":
        return Step(step_dict.get(cls.ACTION_KEY),
                    step_dict.get(cls.DESC_KEY),
                    step_dict.get(cls.WHERE_KEY),
                    step_dict.get(cls.EXPECT_KEY))

    def __init__(self, action: str, description: str, where: Dict,
                 expect: List[Dict] = None):
        self.action = action
        self.description = description
        self.where = where
        self.expect = expect if expect else []

    def is_valid(self) -> bool:
        if self.action and self.where:
            return True
        return False

    def interpolate_with_parameters(self, parameters):
        where_template = Template(json.dumps(self.where))
        self.where = json.loads(where_template.render(parameters))

    def get_where_clause_template_variables(self):
        env = Environment()
        ast = env.parse(json.dumps(self.where))
        return meta.find_undeclared_variables(ast)

    def __eq__(self, o: "Step") -> bool:
        return self.action == o.action and self.description == o.description \
               and self.where == o.where

    def items(self) -> List[Tuple]:
        list_of_tuples = []
        if self.description:
            list_of_tuples.append((Step.DESC_KEY, self.description))
        list_of_tuples += [(Step.ACTION_KEY, self.action),
                           (Step.WHERE_KEY, self.where)]
        return list_of_tuples

    def to_dict(self) -> Dict:
        step_dict = {Step.ACTION_KEY: self.action, Step.WHERE_KEY: self.where}
        if self.description:
            step_dict[Step.DESC_KEY] = self.description
        if self.expect:
            step_dict[Step.EXPECT_KEY] = self.expect
        return step_dict

    @staticmethod
    def encode_step(step: "Step") -> Dict:
        if isinstance(step, Step):
            return step.to_dict()
        else:
            type_name = step.__class__.__name__
            raise TypeError(f"Object of type '{type_name}' is not JSON "
                            f"serializable using Step.encode_step")

    @staticmethod
    def convert_to_steps(steps_list: List[Dict]) -> List["Step"]:
        steps = []
        invalid_steps = []
        for step_dict in steps_list:
            step = Step.build(step_dict)
            if step.is_valid():
                steps.append(step)
            else:
                invalid_steps.append(step_dict)
        if invalid_steps:
            raise ValidationError(
                message="Invalid Steps: Some steps provided are invalid. "
                        "Invalid Steps: " + json.dumps(invalid_steps),
                code="invalid")
        return steps

    def get_namespace(self):
        return self.action.split('.')[0]

    def get_function_name(self):
        parts = self.action.split('.')
        return '.'.join(parts[1:])
