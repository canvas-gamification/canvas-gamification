from rest_framework import serializers

from course.models.parsons_question import ParsonsQuestion


class ParsonsQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsonsQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'difficulty', 'is_verified', 'variables', 'lines', 'junit_template',
                  'additional_file_name']
