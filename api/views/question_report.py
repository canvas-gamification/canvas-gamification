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
        unclear_description = request.data.get('unclearDescription')
        test_case_incorrect_answer = request.data.get('test_case_incorrect_answer')
        poor_test_coverage = request.data.get('poor_test_coverage')
        language_specific = request.data.get('language_specific')
        other = request.data.get('other')
        report_text = request.data.get('report_text')

        QuestionReport.unclear_description = unclear_description
        QuestionReport.test_case_incorrect_answer = test_case_incorrect_answer
        QuestionReport.poor_test_coverage = poor_test_coverage
        QuestionReport.language_specific = language_specific
        QuestionReport.other = other
        QuestionReport.report_text = report_text
        QuestionReport.save()
        return Response(request.data)

