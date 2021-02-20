from rest_framework import viewsets

from api.permissions import TeacherAccessPermission
from api.serializers import QuestionSerializer
from course.models.models import Question


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [TeacherAccessPermission, ]
