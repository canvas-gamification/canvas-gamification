from rest_framework import serializers

from api.serializers import EventSerializer
from accounts.models import MyUser
from course.models.models import TestModel

class TestSerializer(serializers.ModelSerializer):

    class Meta:

        ## Use with TestModel
        model = TestModel
        fields = ['username', 'tokens', 'team', 'streak']


