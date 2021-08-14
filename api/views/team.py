from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from api.serializers.team import TeamSerializer
from api.permissions import HasDeletePermission, TeacherAccessPermission
from canvas.models import Team, TeamRegistration, CanvasCourse, MyUser
from canvas.utils.utils import get_team_registration


class TeamViewSet(viewsets.ModelViewSet):

    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, ]
    search_fields = ['name', ]
    def get_queryset(self, *args):
        course_id = self.request.query_params.get('courseId', None)
        course = get_object_or_404(CanvasCourse, pk=course_id)
        return Team.objects.filter(course=course)

    @action(detail=True, methods=['get'])
    def get_team_registration(self, request, pk=None):

        course = get_object_or_404(CanvasCourse, pk=pk)
        user = request.user
        try:
            team_reg = TeamRegistration.objects.get(user=user, team__course=course)
        except ObjectDoesNotExist:
            return Response({
                'user_id': user.id,
                'team_id': -1
            })


        # pass whole object to front-end
        return Response(self.get_serializer(team_reg).data)

    
    def create(self, request):
        """
        This endpoint completes team creation and registers the user creating the team in the course
        """
        # get the team name from the request
        team_name = request.data.get("name", None)
        course_id = request.data.get("course_id", None)
        course = get_object_or_404(CanvasCourse, pk=course_id)

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

        return Response(status=status.HTTP_201_CREATED)

    
    def update(self, request, pk=None):
        """
        This endpoint completes team registration for this (user, team) pair
        """
        team = get_object_or_404(Team, pk=pk)
        course = team.course

        # users team registration in this course
        # or team_registration object that does not point to a team
        # a null team will exist if the user previously joined, then left a team
        team_reg = TeamRegistration.objects.filter(user=request.user, team__course=course) | TeamRegistration.objects.filter(user=request.user, team=None)

        # if the user is not registered in any team in this course
        # create a team_registration
        if not team_reg.exists():
            # create a TeamRegistration for this (user, team) pair
            team_reg = TeamRegistration(user=request.user, team=team)
            team_reg.save()

            return Response(status=status.HTTP_200_OK)

        # if the user is/was registered in a team 
        # update their team_registration
        else:
            team_reg.update(team=team)

            return Response(status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        This endpoint completes leaving a team for this (user, team) pair
        """
        team = get_object_or_404(Team, pk=kwargs['pk'])
        team_reg = get_team_registration(user=request.user, team=team)

        if team_reg is not None:
            team_reg.team = None
            team_reg.save()

        return Response(status=status.HTTP_200_OK)
