from rest_framework import serializers

from api.serializers import QuestionSerializer
from course.models.parsons_question import ParsonsQuestion, ParsonsSubmission


class ParsonsQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsonsQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'difficulty', 'is_verified', 'variables', 'lines', 'junit_template',
                  'additional_file_name', 'token_value', 'success_rate', 'type_name', 'event', 'is_sample',
                  'category_name', 'parent_category_name', 'course_name', 'event_name', 'author_name', ]

        lines = serializers.JSONField()
        variables = serializers.JSONField()


class ParsonsSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsonsSubmission
        fields = ['pk', 'submission_time', 'answer', 'grade', 'is_correct', 'is_partially_correct', 'finalized',
                  'status', 'tokens_received', 'token_value', 'question']

    question = QuestionSerializer()
