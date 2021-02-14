from rest_framework import viewsets

from api.serializers import QuestionCategorySerializer
from course.models.models import QuestionCategory


class QuestionCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuestionCategory.objects.all()
    serializer_class = QuestionCategorySerializer
