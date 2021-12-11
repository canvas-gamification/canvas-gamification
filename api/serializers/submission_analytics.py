from rest_framework import serializers

from analytics.models import JavaSubmissionAnalytics, ParsonsSubmissionAnalytics, MCQSubmissionAnalytics
from analytics.models.java import JavaQuestionAnalytics
from analytics.models.mcq import MCQQuestionAnalytics
from analytics.models.models import SubmissionAnalytics, QuestionAnalytics
from analytics.models.parsons import ParsonsQuestionAnalytics


class SubmissionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionAnalytics
        fields = '__all__'

        depth = 1


class JavaSubmissionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JavaSubmissionAnalytics
        fields = '__all__'

        depth = 1


class ParsonsSubmissionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsonsSubmissionAnalytics
        fields = '__all__'

        depth = 1


class MCQSubmissionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCQSubmissionAnalytics
        fields = '__all__'

        depth = 1


class QuestionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAnalytics
        fields = '__all__'

        depth = 1


class JavaQuestionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JavaQuestionAnalytics
        fields = '__all__'

        depth = 1


class ParsonsQuestionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsonsQuestionAnalytics
        fields = '__all__'

        depth = 1


class MCQQuestionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCQQuestionAnalytics
        fields = '__all__'

        depth = 1
