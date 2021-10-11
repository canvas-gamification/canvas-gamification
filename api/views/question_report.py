from rest_framework import viewsets
from general.models.question_report import QuestionReport
from rest_framework.permissions import IsAuthenticated
from api.serializers import QuestionReportSerializer


class QuestionReportViewSet(viewsets.ModelViewSet):
    queryset = QuestionReport.objects.all()
    serializer_class = QuestionReportSerializer
    permission_classes = [IsAuthenticated, ]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


