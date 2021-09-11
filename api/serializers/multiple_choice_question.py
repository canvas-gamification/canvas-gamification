from rest_framework import serializers

import api.error_messages as ERROR_MESSAGES
from api.serializers import QuestionSerializer
from course.models.multiple_choice import MultipleChoiceQuestion, MultipleChoiceSubmission


class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.TITLE.ERROR_MESSAGES)
    text = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.TEXT.ERROR_MESSAGES)
    difficulty = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.DIFFICULTY.ERROR_MESSAGES)
    answer = serializers.CharField(required=True, error_messages=ERROR_MESSAGES.ANSWER.ERROR_MESSAGES)
    visible_distractor_count = serializers.IntegerField(
        required=True,
        error_messages=ERROR_MESSAGES.VISIBLE_DISTRACTOR_COUNT.ERROR_MESSAGES)
    choices = serializers.JSONField()
    variables = serializers.JSONField()

    class Meta:
        model = MultipleChoiceQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'difficulty', 'is_verified', 'variables', 'choices', 'visible_distractor_count',
                  'token_value', 'success_rate', 'type_name', 'event', 'is_sample', 'category_name',
                  'parent_category_name', 'course_name', 'event_name', 'author_name', 'is_checkbox']


class MultipleChoiceSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleChoiceSubmission
        fields = ['pk', 'submission_time', 'answer', 'grade', 'is_correct', 'is_partially_correct', 'finalized',
                  'status', 'tokens_received', 'token_value', 'question', 'answer_display', 'show_answer',
                  'show_detail', 'status_color']

    question = QuestionSerializer()


class MultipleChoiceSubmissionHiddenDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleChoiceSubmission
        fields = ['pk', 'submission_time', 'answer', 'answer_display', 'token_value', 'question', 'show_answer',
                  'show_detail']

    question = QuestionSerializer()
