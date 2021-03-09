from rest_framework import serializers

from course.models.models import JavaQuestion, JavaSubmission


class JavaQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JavaQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'difficulty', 'is_verified', 'variables', 'junit_template', 'input_file_names']


class JavaSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JavaSubmission
        fields = ['pk', 'submission_time', 'answer', 'grade', 'is_correct', 'is_partially_correct', 'finalized',
                  'status', 'tokens_received', 'token_value', 'answer_files']
