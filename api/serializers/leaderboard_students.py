from rest_framework import serializers

from api.serializers import EventSerializer
from accounts.models import MyUser
from course.models.models import LeaderBoardStudents

class LeaderBoardStudentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaderBoardStudents
        fields = ['student', 'token_value', 'team', 'streak']
