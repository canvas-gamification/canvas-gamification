from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.serializers.team import TeamSerializer
from canvas.models import Team, TeamRegistration, CanvasCourse
from canvas.utils.utils import get_course_registration, get_team_registration



class TeamViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = TeamSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = Team.objects.all()

        return queryset.all()

    @action(detail=True, methods=['post'])
    def create_team(self, request, pk=None):
        """
        This endpoint completes team creation and registers the user creating the team in the course 
        """

        # get the team name from the request
        team_name = request.data.get("name", None)

        course = get_object_or_404(CanvasCourse, pk=pk)


        # create a new team with the specified name
        new_team = Team(name=team_name, course=course)
        new_team.save()

        # register the creator of the team to the team
        new_team_reg = TeamRegistration(user=request.user, team=new_team)
        new_team_reg.save()
        
        return Response({
                "status": "Created",
            })
            
    @action(detail=True, methods=['post'])
    def join_team(self, request, pk=None):
        """
        This endpoint completes team registration for this (user, team) pair
        """
        team = get_object_or_404(Team, pk=pk)
        team_reg = get_team_registration(user=request.user, team=team)

        if team_reg is None:
            # create a TeamRegistration for this (user, team) pair if one does not already exist
            team_reg = TeamRegistration(user=request.user, team=team)
            team_reg.save()

        return Response({
                "status": "Registered",
            })
        