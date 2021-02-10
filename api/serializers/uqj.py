from rest_framework import serializers

from course.models.models import UserQuestionJunction


class UQJSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuestionJunction
        exclude = ['user']
        depth = 1
