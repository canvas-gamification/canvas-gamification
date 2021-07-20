from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.serializers.team import TeamSerializer
from canvas.models import Team, TeamRegistration, CanvasCourse
from canvas.utils.utils import get_course_registration



class TeamViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = TeamSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = Team.objects.all()

        return queryset.all()

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        name = request.data.get("name", None)
        course = get_object_or_404(CanvasCourse, pk=pk)

        new_team = Team(name=name, course=course)
        new_team.save()
        return Response({
                "status": "Created",
            })