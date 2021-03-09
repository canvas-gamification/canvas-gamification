from rest_framework import serializers

from course.models.models import MultipleChoiceQuestion, MultipleChoiceSubmission


class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleChoiceQuestion
        fields = ['id', 'title', 'text', 'answer', 'max_submission_allowed', 'time_created', 'time_modified', 'author',
                  'category', 'difficulty', 'is_verified', 'variables', 'choices', 'visible_distractor_count']


class MultipleChoiceSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleChoiceSubmission
        fields = ['pk', 'submission_time', 'answer', 'grade', 'is_correct', 'is_partially_correct', 'finalized',
                  'status', 'tokens_received', 'token_value']
