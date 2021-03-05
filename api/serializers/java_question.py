from rest_framework import serializers

from course.models.models import JavaQuestion


class JavaQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JavaQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'difficulty', 'is_verified', 'variables', 'junit_template', 'input_file_names']
