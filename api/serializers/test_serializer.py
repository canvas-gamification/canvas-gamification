from rest_framework import serializers

from api.serializers import EventSerializer
from course.models.models import TestModel

class TestSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestModel
        fields = ['user', 'tokens']

