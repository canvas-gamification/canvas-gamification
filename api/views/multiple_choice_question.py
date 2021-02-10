from rest_framework import viewsets

from api.serializers import MultipleChoiceQuestionSerializer
from course.models.models import MultipleChoiceQuestion


class SampleMultipleChoiceQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MultipleChoiceQuestion.objects.filter(is_sample=True).all()
    serializer_class = MultipleChoiceQuestionSerializer
