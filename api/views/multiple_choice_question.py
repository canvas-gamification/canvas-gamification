from rest_framework import viewsets

from api.pagination import BasePagination
from api.permissions import TeacherAccessPermission
from api.serializers import MultipleChoiceQuestionSerializer
from course.models.models import MultipleChoiceQuestion


class SampleMultipleChoiceQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MultipleChoiceQuestion.objects.filter(is_sample=True).all()
    serializer_class = MultipleChoiceQuestionSerializer


class MultipleChoiceQuestionViewSet(viewsets.ModelViewSet):
    queryset = MultipleChoiceQuestion.objects.all()
    permission_classes = [TeacherAccessPermission]
    serializer_class = MultipleChoiceQuestionSerializer
    pagination_class = BasePagination
