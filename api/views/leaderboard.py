
from rest_framework import viewsets


from course.models.models import LeaderBoard
from api.serializers.leaderboard import LeaderBoardSerializer

class LeaderBoardViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # return MyUser.objects.all() #Use with actual users in database

        return LeaderBoard.objects.all()
    serializer_class = LeaderBoardSerializer
