from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import MyUser
from course.models.models import Question
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
        report_details = request.data.get('report_details')
        user_instance = request.data.get('user')
        user = MyUser.objects.all().filter(username=user_instance.get('username')).get()
        question_instance = request.data.get('question')
        question = Question.objects.all().filter(id=question_instance.get('id')).get()
        question_report = QuestionReport(report=report, report_details=report_details, user=user, question=question)
        question_report.save()
        return Response(request.data)

