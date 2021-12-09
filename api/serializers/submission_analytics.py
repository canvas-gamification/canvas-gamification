from rest_framework import serializers

from analytics.models.models import SubmissionAnalytics, QuestionAnalytics


class SubmissionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionAnalytics
        fields = '__all__'

        depth = 1
