from rest_framework import serializers
from general.models.question_report import QuestionReport


class QuestionReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuestionReport
        fields = ['id', 'created_at', 'updated_at', 'typo_in_question', 'typo_in_answer',
                  'correct_solution_marked_wrong', 'incorrect_solution_marked_right', 'other',
                  'report_details']
