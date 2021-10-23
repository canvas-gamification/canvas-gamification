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
    def create_report(self, request, pk=None):
        report = request.data.get('report')
        QuestionReport.report_details = report
        QuestionReport.save()
        return Response(request.data)

