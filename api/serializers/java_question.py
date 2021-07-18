from rest_framework import serializers

import api.error_messages as ERROR_MESSAGES
from api.serializers import QuestionSerializer
from course.models.models import JavaQuestion, JavaSubmission


class JavaQuestionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.TITLE.ERROR_MESSAGES)
    text = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.TEXT.ERROR_MESSAGES)
    difficulty = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.DIFFICULTY.ERROR_MESSAGES)
    junit_template = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.JUNIT_TEMPLATE.ERROR_MESSAGES)
    input_file_names = serializers.JSONField(
        required=True, error_messages=ERROR_MESSAGES.INPUT_FILE_NAMES.ERROR_MESSAGES)
    variables = serializers.JSONField()

    class Meta:
        model = JavaQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'difficulty', 'is_verified', 'variables', 'junit_template', 'input_file_names',
                  'token_value', 'success_rate', 'type_name', 'event', 'is_sample', 'category_name',
                  'parent_category_name', 'course_name', 'event_name', 'author_name']


class JavaSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JavaSubmission
        fields = ['pk', 'submission_time', 'answer', 'grade', 'is_correct', 'is_partially_correct', 'finalized',
                  'status', 'tokens_received', 'token_value', 'answer_files', 'question', 'get_decoded_stderr',
                  'get_decoded_results', 'get_formatted_test_results', 'get_passed_test_results',
                  'get_failed_test_results', 'get_num_tests', 'formatted_tokens_received', 'show_answer', 'show_detail',
                  'status_color']

    question = QuestionSerializer()
