from rest_framework import serializers

import api.error_messages as ERROR_MESSAGES
from api.serializers import QuestionSerializer, EventSerializer, QuestionCategorySerializer
from canvas.models import Event
from course.models.java import JavaQuestion, JavaSubmission
from course.models.models import QuestionCategory


class JavaQuestionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.TITLE.ERROR_MESSAGES)
    text = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.TEXT.ERROR_MESSAGES)
    difficulty = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.DIFFICULTY.ERROR_MESSAGES)
    junit_template = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.JUNIT_TEMPLATE.ERROR_MESSAGES)
    input_files = serializers.JSONField(
        required=True, error_messages=ERROR_MESSAGES.INPUT_FILES.ERROR_MESSAGES)
    variables = serializers.JSONField()
    event = EventSerializer()
    event_id = serializers.PrimaryKeyRelatedField(source='event', queryset=Event.objects.all())
    category = QuestionCategorySerializer()
    category_id = serializers.PrimaryKeyRelatedField(source='category', queryset=QuestionCategory.objects.all())

    class Meta:
        model = JavaQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'category_id', 'difficulty', 'is_verified', 'variables', 'junit_template', 'input_files',
                  'token_value', 'success_rate', 'type_name', 'event', 'event_id', 'is_sample', 'parent_category_name',
                  'course', 'author_name']


class JavaSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JavaSubmission
        fields = ['pk', 'submission_time', 'answer', 'grade', 'is_correct', 'is_partially_correct', 'finalized',
                  'status', 'tokens_received', 'token_value', 'answer_files', 'question', 'get_decoded_stderr',
                  'get_decoded_results', 'get_status_message', 'get_formatted_test_results', 'get_passed_test_results',
                  'get_failed_test_results', 'get_num_tests', 'formatted_tokens_received', 'show_answer', 'show_detail',
                  'status_color']

    question = QuestionSerializer()
