from api import serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist


from api.serializers.team import TeamSerializer
from canvas.models import Team, TeamRegistration, CanvasCourse, MyUser
from canvas.utils.utils import get_course_registration, get_team_registration


class TeamViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = TeamSerializer

    def get_queryset(self, *args):
        courseId = self.request.query_params.get('courseId', None)
        course = get_object_or_404(CanvasCourse, pk=courseId)
        queryset = Team.objects.all()
        queryset = queryset.filter(course=course)
        return queryset.all()


    @action(detail=True, methods=['get'])
    def get_team_registration(self, request, pk=None):
        
        course = get_object_or_404(CanvasCourse, pk=pk)
        userId = self.request.query_params.get('userId', None)
        user = get_object_or_404(MyUser, pk=userId)
        try:
            team_reg = TeamRegistration.objects.get(user=user, team__course=course)
        except ObjectDoesNotExist:
            return Response({
                'userId': userId,
                'teamId': -1
            })
       
        return Response({
            'userId': team_reg.user.id,
            'teamId': team_reg.team.id
        })


    @action(detail=True, methods=['post'])
    def create_team(self, request, pk=None):
        """
        This endpoint completes team creation and registers the user creating the team in the course 
        """

        # get the team name from the request
        team_name = request.data.get("name", None)

        course = get_object_or_404(CanvasCourse, pk=pk)

        # all teams registrations for the user in the requested course
        all_team_reg = TeamRegistration.objects.filter(user=request.user, team__course=course)
        
        # delete other registrations if any exist
        if(all_team_reg is not None):
                for reg in all_team_reg:
                    reg.delete()

                    
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

        course = team.course
        
        # all teams registrations for the user in the requested course
        all_team_reg = TeamRegistration.objects.filter(user=request.user, team__course=course)
        

        # if the user is not registered for the selected team
        if team_reg is None:
            # delete other registrations if any exist already
            if(all_team_reg is not None):
                for reg in all_team_reg:
                    reg.delete()

            # create a TeamRegistration for this (user, team) pair if one does not already exist
            team_reg = TeamRegistration(user=request.user, team=team)
            team_reg.save()

        return Response({
                "status": "Registered",
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

        return Response({
                "status": "De-registered",
            })