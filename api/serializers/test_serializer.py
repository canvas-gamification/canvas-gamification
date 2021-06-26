from rest_framework import serializers

from api.serializers import EventSerializer
from accounts.models import MyUser
from course.models.models import TestModel

class TestSerializer(serializers.ModelSerializer):

    class Meta:
<<<<<<< HEAD
        ## Use with MyUser model
        # model = MyUser
        # fields = ['first_name', 'tokens']

        ## Use with TestModel
        model = TestModel
        fields = ['username', 'tokens']
=======

        ## Use with TestModel
        model = TestModel
        fields = ['username', 'tokens', 'hotStreak', 'coldStreak']
>>>>>>> fbccc132012d5eb31b8d55af1e0be7af3268a2b8

