from rest_framework import serializers
from general.models.question_report import QuestionReport


class QuestionReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionReport
        fields = ['id', 'question', 'created_at', 'updated_at', 'report', 'report_details']
