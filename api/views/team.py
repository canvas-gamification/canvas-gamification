from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from api.serializers.team import TeamSerializer
from canvas.models import Team, TeamRegistration, CanvasCourse, MyUser
from canvas.utils.utils import get_team_registration


class TeamViewSet(viewsets.ModelViewSet):

    serializer_class = TeamSerializer

    def get_queryset(self, *args):
        course_id = self.request.query_params.get('courseId', None)
        course = get_object_or_404(CanvasCourse, pk=course_id)
        return Team.objects.filter(course=course)

    @action(detail=True, methods=['get'])
    def get_team_registration(self, request, pk=None):

        course = get_object_or_404(CanvasCourse, pk=pk)
        user_id = self.request.query_params.get('userId', None)
        user = get_object_or_404(MyUser, pk=user_id)
        try:
            team_reg = TeamRegistration.objects.get(user=user, team__course=course)
        except ObjectDoesNotExist:
            return Response({
                'user_id': user_id,
                'team_id': -1
            })

        return Response({
            'user_id': team_reg.user.id,
            'team_id': team_reg.team.id
        })

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

        # see if the user is already registered in a team
        team_reg = TeamRegistration.objects.filter(user=request.user, team__course=course)

        # if user is already registered in a team
        # update the team_registration record
        if team_reg is not None:
            # update team_registration record
            team_reg.update(team=new_team)

        # if the user does not have a team registration
        # create one
        else:
            # register the creator of the team to the team
            new_team_reg = TeamRegistration(user=request.user, team=new_team)
            new_team_reg.save()

        return Response({
            200
        })

    @action(detail=True, methods=['post'])
    def join_team(self, request, pk=None):
        """
        This endpoint completes team registration for this (user, team) pair
        """
        team = get_object_or_404(Team, pk=pk)
        course = team.course

        # users team registration in this course
        team_reg = TeamRegistration.objects.filter(user=request.user, team__course=course)

        # if the user is not registered in any team in this course
        # create a team_registration
        if not team_reg.exists():
            # create a TeamRegistration for this (user, team) pair
            team_reg = TeamRegistration(user=request.user, team=team)
            team_reg.save()

            return Response({
                200
            })

        # if the user is registered in a team already
        # update their team_registration
        else:
            team_reg.update(team=team)

            return Response({
                'status': 200
            })

    @action(detail=True, methods=['post'])
    def leave_team(self, request, pk=None):
        """
        This endpoint completes leaving a team for this (user, team) pair
        """
        team = get_object_or_404(Team, pk=pk)
        team_reg = get_team_registration(user=request.user, team=team)

        if team_reg is None:
            pass

        else:
            team_reg.delete()

        return Response({200})
