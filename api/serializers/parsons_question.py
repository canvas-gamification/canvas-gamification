from rest_framework import serializers

import api.error_messages as ERROR_MESSAGES
from api.serializers import QuestionSerializer
from course.models.parsons_question import ParsonsQuestion, ParsonsSubmission


class ParsonsQuestionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.TITLE.ERROR_MESSAGES)
    text = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.TEXT.ERROR_MESSAGES)
    difficulty = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.DIFFICULTY.ERROR_MESSAGES)
    junit_template = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.JUNIT_TEMPLATE.ERROR_MESSAGES)
    lines = serializers.JSONField(required=True, error_messages=ERROR_MESSAGES.LINES.ERROR_MESSAGES)
    additional_file_name = serializers.CharField(
        required=True, error_messages=ERROR_MESSAGES.ADDITIONAL_FILE_NAME.ERROR_MESSAGES)
    variables = serializers.JSONField()

    class Meta:
        model = ParsonsQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'difficulty', 'is_verified', 'variables', 'lines', 'junit_template',
                  'additional_file_name', 'token_value', 'success_rate', 'type_name', 'event', 'is_sample',
                  'category_name', 'parent_category_name', 'course_name', 'event_name', 'author_name', ]


class ParsonsSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsonsSubmission
        fields = ['pk', 'submission_time', 'answer', 'grade', 'is_correct', 'is_partially_correct', 'finalized',
                  'status', 'tokens_received', 'token_value', 'question', 'no_file_answer', 'get_decoded_stderr',
                  'get_decoded_results', 'get_formatted_test_results', 'get_passed_test_results',
                  'get_failed_test_results', 'get_num_tests', 'formatted_tokens_received', 'answer_files',
                  'show_answer', 'show_detail', 'status_color']

    question = QuestionSerializer()
