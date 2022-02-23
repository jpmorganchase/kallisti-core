import json
from json.decoder import JSONDecodeError

from django.core.exceptions import ValidationError
from django.db import models
from kallisticore.models.step import Step


class ListField(models.TextField):
    description = "ListField automatically serializes\\deserializes values " \
                  "to\\from JSON."

    def from_db_value(self, value, expression=None, connection=None):
        return self._parse_list(value)

    def to_python(self, value):
        if isinstance(value, list):
            return value
        return self._parse_list(value)

    def get_prep_value(self, value):
        if isinstance(value, list):
            return json.dumps(value)
        return json.dumps(json.loads(value))

    def _parse_list(self, value):
        if value is None or value == "":
            return []
        try:
            return json.loads(value)
        except JSONDecodeError as e:
            error_message = "Invalid format: " + e.msg
            raise ValidationError(error_message)


class StepsField(ListField):
    def from_db_value(self, value, expression=None, connection=None):
        value = super().from_db_value(value, expression, connection)
        return Step.convert_to_steps(value)

    def to_python(self, value):
        value = super().to_python(value)
        if isinstance(value, list) and all(isinstance(x, Step) for x in value):
            return value
        return Step.convert_to_steps(value)

    def get_prep_value(self, value):
        if isinstance(value, list):
            return json.dumps(
                [Step.build(item) if isinstance(item, dict) else item
                 for item in value],
                default=Step.encode_step)
        return json.dumps(json.loads(value))


class DictField(models.TextField):
    description = "DictField automatically serializes\\deserializes values " \
                  "to\\from JSON."

    def from_db_value(self, value, expression=None, connection=None):
        return self._parse_dict(value)

    def to_python(self, value):
        if isinstance(value, dict):
            return value
        return self._parse_dict(value)

    def get_prep_value(self, value):
        if isinstance(value, dict):
            return json.dumps(value)
        return json.dumps(json.loads(value))

    def _parse_dict(self, value):
        if value is None or value == "":
            return {}
        try:
            return json.loads(value)
        except JSONDecodeError as e:
            error_message = "Invalid format: " + e.msg
            raise ValidationError(error_message)
