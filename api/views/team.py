from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.permissions import TeamPermission
from api.serializers.team import TeamSerializer
from canvas.models.models import Event
from canvas.models.team import Team
from canvas.services.team import create_and_join_team, join_team, get_my_team


class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = [TeamPermission]
    serializer_class = TeamSerializer
    queryset = Team.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["event"]

    @action(detail=False, methods=["post"], url_path="create-and-join")
    def create_and_join(self, request):
        event_id = request.data.get("event_id", None)
        name = request.data.get("name", None)
        is_private = request.data.get("is_private", None)
        who_can_join = request.data.get("who_can_join", None)
        event = get_object_or_404(Event, id=event_id)
        team = create_and_join_team(event, request.user, name, is_private, who_can_join)

        serializer = self.get_serializer(team)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="join")
    def join(self, request):
        team_id = request.data.get("team_id", None)
        team = get_object_or_404(Team, id=team_id)

        join_team(team, request.user)

        return Response({"status": "success"})

    @action(detail=False, methods=["get"], url_path="my-team")
    def my_team(self, request):
        event_id = request.GET.get("event_id", None)
        event = get_object_or_404(Event, id=event_id)

        team = get_my_team(event, request.user)

        serializer = self.get_serializer(team)
        return Response(serializer.data)
