from rest_framework import serializers

from api.serializers import QuestionSerializer
from course.models.parsons_question import ParsonsQuestion, ParsonsSubmission


class ParsonsQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsonsQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'difficulty', 'is_verified', 'variables', 'junit_template', 'token_value', 'success_rate',
                  'type_name', 'event', 'is_sample', 'category_name', 'parent_category_name', 'course_name',
                  'event_name', 'author_name', 'input_files']

        lines = serializers.JSONField()
        variables = serializers.JSONField()


class ParsonsSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsonsSubmission
        fields = ['pk', 'submission_time', 'answer', 'grade', 'is_correct', 'is_partially_correct', 'finalized',
                  'status', 'tokens_received', 'token_value', 'question', 'get_decoded_stderr', 'get_decoded_results',
                  'get_formatted_test_results', 'get_passed_test_results', 'get_failed_test_results', 'get_num_tests',
                  'formatted_tokens_received', 'answer_files', 'show_answer', 'show_detail', 'status_color']

    question = QuestionSerializer()
