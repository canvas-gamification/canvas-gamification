from rest_framework import serializers

from analytics.models import JavaSubmissionAnalytics, MCQSubmissionAnalytics, ParsonsSubmissionAnalytics
from analytics.models.models import SubmissionAnalytics


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


class MCQSubmissionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCQSubmissionAnalytics
        fields = '__all__'

        depth = 1


class ParsonsSubmissionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsonsSubmissionAnalytics
        fields = '__all__'

        depth = 1
