from rest_framework import serializers

from course.models.models import ReportQuestion, Question


class ReportQuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportQuestion
        fields = ['question_id', 'report_timestamp', 'is_report',  'report_text']

