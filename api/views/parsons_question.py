from rest_framework import viewsets

from api.pagination import BasePagination
from api.permissions import TeacherAccessPermission
from api.serializers import ParsonsQuestionSerializer
from course.models.parsons import ParsonsQuestion


class ParsonsQuestionViewSet(viewsets.ModelViewSet):
    queryset = ParsonsQuestion.objects.all()
    permission_classes = [TeacherAccessPermission]
    serializer_class = ParsonsQuestionSerializer
    pagination_class = BasePagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
