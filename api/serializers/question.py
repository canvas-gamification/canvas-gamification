from rest_framework import serializers

from course.models.models import Question


class QuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Question
        fields = ['title', 'max_submission_allowed', 'time_created', 'time_modified', 'author', 'category',
                  'difficulty', 'is_verified', 'token_value', 'success_rate', 'type_name', 'event']
        depth = 1
