from rest_framework import serializers
from canvas.models import CanvasCourse


class CourseNamesSerializer(serializers.ModelSerializer):

    class Meta:
        model = CanvasCourse
        fields = ['name']
