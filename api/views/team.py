from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.serializers.team import TeamSerializer
from canvas.models.models import Event
from canvas.models.team import Team
from canvas.services.team import create_and_join_team, join_team


class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = []
    serializer_class = TeamSerializer
    queryset = Team.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["event"]

    @action(detail=False, methods=["post"], url_path="create-and-join")
    def create_and_join(self, request):
        event_id = request.data.get("event_id", None)
        name = request.data.get("name", None)
        event = get_object_or_404(Event, id=event_id)
        team = create_and_join_team(event, request.user, name)

        serializer = self.get_serializer(team)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="join")
    def join(self, request):
        team_id = request.data.get("team_id", None)
        team = get_object_or_404(Team, id=team_id)

        join_team(team, request.user)

        return Response({"status": "success"})
