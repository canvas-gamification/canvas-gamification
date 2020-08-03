import jsonfield
import json


class JSONField(jsonfield.JSONField):
    pass


class JSONFormField(jsonfield.fields.JSONFormField):
    def prepare_value(self, value):
        if type(value) != str:
            return json.dumps(value)
        return value


class JSONLineFormField(JSONFormField):
    def to_python(self, value):
        return [x for x in value.splitlines()]

    def prepare_value(self, value):
        if type(value) == list:
            return "\n".join(value)
        return value
