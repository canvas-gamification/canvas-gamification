
from rest_framework import viewsets


from course.models.models import LeaderBoardStudents
from api.serializers.leaderboard_students import LeaderBoardStudentsSerializer

class LeaderBoardStudentsViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # return MyUser.objects.all() #Use with actual users in database

        return LeaderBoardStudents.objects.all()
    serializer_class = LeaderBoardStudentsSerializer
