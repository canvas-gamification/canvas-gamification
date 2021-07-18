import json

from django.template.loader import render_to_string
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.response import Response

import api.error_messages as ERROR_MESSAGES
from api.permissions import TeacherAccessPermission


class SchemaViewSet(viewsets.ViewSet):
    permission_classes = [TeacherAccessPermission]
    schema_list = ['java_input_files', 'parsons_input_files', 'test_cases', 'variables']

    def get_schema(self, name):
        if name not in self.schema_list:
            raise serializers.ValidationError(ERROR_MESSAGES.SCHEMA.INVALID)
        return json.loads(render_to_string('schemas/{}.json'.format(name)))

    def list(self, request):
        return Response([self.get_schema(x) for x in self.schema_list])

    def retrieve(self, request, pk=None):
        return Response(self.get_schema(pk))
