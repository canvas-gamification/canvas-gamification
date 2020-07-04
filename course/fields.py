import jsonfield
import json


class JSONField(jsonfield.JSONField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return json.loads(value, **self.decoder_kwargs)


class JSONFormField(jsonfield.fields.JSONFormField):
    def prepare_value(self, value):
        return str(value).replace("'", "\"")
