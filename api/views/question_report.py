from rest_framework import viewsets, status

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers import QuestionReportSerializer
from general.models.question_report import QuestionReport
from general.services.action import create_question_report_action


class QuestionReportViewSet(viewsets.ModelViewSet):
    queryset = QuestionReport.objects.all()
    serializer_class = QuestionReportSerializer
    permission_classes = [IsAuthenticated, ]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        create_question_report_action(serializer.data, self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
