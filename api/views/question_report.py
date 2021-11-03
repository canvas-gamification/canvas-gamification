from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated
from api.serializers import QuestionReportSerializer
from general.services.action import create_question_report_action


class QuestionReportViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionReportSerializer
    permission_classes = [IsAuthenticated, ]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        create_question_report_action(serializer.data, self.request.user)
