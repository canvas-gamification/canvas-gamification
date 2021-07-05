import json

from django.template.loader import render_to_string
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from api.permissions import TeacherAccessPermission


class SchemaViewSet(viewsets.ViewSet):
    permission_classes = [TeacherAccessPermission]
    schema_list = ['input_file_names', 'parsons_input_files', 'test_cases', 'variables']

    def get_schema(self, name):
        if name not in self.schema_list:
            raise NotFound()
        return json.loads(render_to_string('schemas/{}.json'.format(name)))

    def list(self, request):
        return Response([self.get_schema(x) for x in self.schema_list])

    def retrieve(self, request, pk=None):
        return Response(self.get_schema(pk))
