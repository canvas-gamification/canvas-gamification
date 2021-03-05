from rest_framework import viewsets

from api.pagination import BasePagination
from api.permissions import QuestionAccessPermission
from api.serializers import ParsonsQuestionSerializer
from course.models.parsons_question import ParsonsQuestion


class ParsonsQuestionViewSet(viewsets.ModelViewSet):
    queryset = ParsonsQuestion.objects.all()
    permission_classes = [QuestionAccessPermission]
    serializer_class = ParsonsQuestionSerializer
    pagination_class = BasePagination
