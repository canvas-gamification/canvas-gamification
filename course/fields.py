import jsonfield


class JSONField(jsonfield.JSONField):
    pass


class JSONFormField(jsonfield.fields.JSONFormField):
    def prepare_value(self, value):
        return str(value).replace("'", "\"")


class JSONLineFormField(JSONFormField):
    def to_python(self, value):
        return [x for x in value.splitlines()]

    def prepare_value(self, value):
        if type(value) == list:
            return "\n".join(value)
        return value
