
from rest_framework import viewsets

from course.models.models import TestModel

from Leader_board.models import LeaderBoardAssignedStudents
from api.serializers import LeaderBoardSerializer

class LeaderBoardViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # return MyUser.objects.all() #Use with actual users in database

        return LeaderBoardAssignedStudents.objects.all()
    serializer_class = LeaderBoardSerializer