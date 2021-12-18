from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

import api.error_messages as ERROR_MESSAGES
from api.serializers import QuestionSerializer, EventSerializer, QuestionCategorySerializer
from course.models.parsons import ParsonsQuestion, ParsonsSubmission


class ParsonsQuestionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.TITLE.ERROR_MESSAGES)
    text = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.TEXT.ERROR_MESSAGES)
    difficulty = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.DIFFICULTY.ERROR_MESSAGES)
    junit_template = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.JUNIT_TEMPLATE.ERROR_MESSAGES)
    input_files = serializers.JSONField(required=True, error_messages=ERROR_MESSAGES.INPUT_FILES.ERROR_MESSAGES)
    variables = serializers.JSONField()
    event_obj = SerializerMethodField('get_event_obj')
    category_obj = SerializerMethodField('get_category_obj')

    class Meta:
        model = ParsonsQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'category_obj', 'difficulty', 'is_verified', 'variables', 'junit_template', 'token_value',
                  'success_rate', 'type_name', 'event', 'event_obj', 'is_sample', 'category_name',
                  'parent_category_name', 'course', 'event_name', 'author_name', 'input_files']

    def get_event_obj(self, question):
        return EventSerializer(question.event).data

    def get_category_obj(self, question):
        return QuestionCategorySerializer(question.category).data


class ParsonsSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsonsSubmission
        fields = ['pk', 'submission_time', 'answer', 'grade', 'is_correct', 'is_partially_correct', 'finalized',
                  'status', 'tokens_received', 'token_value', 'question', 'get_decoded_stderr', 'get_decoded_results',
                  'get_formatted_test_results', 'get_passed_test_results', 'get_failed_test_results', 'get_num_tests',
                  'formatted_tokens_received', 'answer_files', 'show_answer', 'show_detail', 'status_color']

    question = QuestionSerializer()


class ParsonsSubmissionHiddenDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsonsSubmission
        fields = ['pk', 'submission_time', 'answer', 'token_value', 'question', 'answer_files', 'show_answer',
                  'show_detail']

    question = QuestionSerializer()
