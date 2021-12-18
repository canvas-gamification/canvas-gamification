from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

import api.error_messages as ERROR_MESSAGES
from api.serializers import QuestionSerializer, EventSerializer, QuestionCategorySerializer
from course.models.java import JavaQuestion, JavaSubmission


class JavaQuestionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.TITLE.ERROR_MESSAGES)
    text = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.TEXT.ERROR_MESSAGES)
    difficulty = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.DIFFICULTY.ERROR_MESSAGES)
    junit_template = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.JUNIT_TEMPLATE.ERROR_MESSAGES)
    input_files = serializers.JSONField(
        required=True, error_messages=ERROR_MESSAGES.INPUT_FILES.ERROR_MESSAGES)
    variables = serializers.JSONField()
    event_obj = SerializerMethodField('get_event_obj')
    category_obj = SerializerMethodField('get_category_obj')

    class Meta:
        model = JavaQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'category_obj', 'difficulty', 'is_verified', 'variables', 'junit_template', 'input_files',
                  'token_value', 'success_rate', 'type_name', 'event', 'event_obj', 'is_sample', 'parent_category_name',
                  'course', 'author_name']

    def get_event_obj(self, question):
        return EventSerializer(question.event).data

    def get_category_obj(self, question):
        return QuestionCategorySerializer(question.category).data


class JavaSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JavaSubmission
        fields = ['pk', 'submission_time', 'answer', 'grade', 'is_correct', 'is_partially_correct', 'finalized',
                  'status', 'tokens_received', 'token_value', 'answer_files', 'question', 'get_decoded_stderr',
                  'get_decoded_results', 'get_status_message', 'get_formatted_test_results', 'get_passed_test_results',
                  'get_failed_test_results', 'get_num_tests', 'formatted_tokens_received', 'show_answer', 'show_detail',
                  'status_color']

    question = QuestionSerializer()


class JavaSubmissionHiddenDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JavaSubmission
        fields = ['pk', 'submission_time', 'answer', 'token_value', 'answer_files', 'question', 'show_answer',
                  'show_detail']

    question = QuestionSerializer()
