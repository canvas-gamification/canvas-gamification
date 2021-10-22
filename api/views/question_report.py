from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from general.models.question_report import QuestionReport
from rest_framework.permissions import IsAuthenticated
from api.serializers import QuestionReportSerializer


class QuestionReportViewSet(viewsets.ModelViewSet):
    queryset = QuestionReport.objects.all()
    serializer_class = QuestionReportSerializer
    permission_classes = [IsAuthenticated, ]

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['post'], url_path='add-report')
    def add_report(self, request, pk=None):
        typo_in_question = request.data.get('typo_in_question')
        typo_in_answer = request.data.get('typo_in_answer')
        correct_solution_marked_wrong = request.data.get('correct_solution_marked_wrong')
        incorrect_solution_marked_right = request.data.get('incorrect_solution_marked_right')
        other = request.data.get('other')
        report_details = request.data.get('report_details')

        QuestionReport.typo_in_question = typo_in_question
        QuestionReport. typo_in_answer = typo_in_answer
        QuestionReport.correct_solution_marked_wrong = correct_solution_marked_wrong
        QuestionReport.incorrect_solution_marked_right = incorrect_solution_marked_right
        QuestionReport.other = other
        QuestionReport. report_details = report_details
        QuestionReport.save()
        return Response(request.data)

