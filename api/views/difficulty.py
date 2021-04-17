from rest_framework import viewsets
from rest_framework.response import Response

from course.models.models import DIFFICULTY_CHOICES


class DifficultyViewSet(viewsets.ViewSet):

    def list(self, request):
        return Response(DIFFICULTY_CHOICES)
