from rest_framework import serializers

from analytics.models import SubmissionAnalytics, QuestionAnalytics


class SubmissionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionAnalytics
        fields = '__all__'

        depth = 1


class QuestionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAnalytics
        fields = '__all__'

        depth = 1
#
# class EventAnalyticsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EventAnalytics
#         fields = '__all__'
#
#         depth = 1