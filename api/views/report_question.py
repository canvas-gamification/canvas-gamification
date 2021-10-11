from rest_framework import viewsets
from course.models.models import ReportQuestion
from rest_framework.permissions import IsAuthenticated
from api.serializers import ReportQuestionSerializer


class ReportQuestionViewSet(viewsets.ModelViewSet):
    queryset = ReportQuestion.objects.all()
    serializer_class = ReportQuestionSerializer
    permission_classes = [IsAuthenticated, ]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


