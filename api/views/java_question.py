from rest_framework import viewsets

from api.pagination import BasePagination
from api.permissions import QuestionAccessPermission
from api.serializers import JavaQuestionSerializer
from course.models.models import JavaQuestion


class JavaQuestionViewSet(viewsets.ModelViewSet):
    queryset = JavaQuestion.objects.all()
    permission_classes = [QuestionAccessPermission]
    serializer_class = JavaQuestionSerializer
    pagination_class = BasePagination
