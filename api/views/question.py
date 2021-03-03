from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters

from api.permissions import TeacherAccessPermission
from api.serializers import QuestionSerializer
from api.pagination import BasePagination
from course.models.models import Question


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Optional Parameters
    ?status: boolean => filter by status
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [TeacherAccessPermission, ]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend]
    ordering_fields = ['author', 'category', 'difficulty', 'course', 'event', 'is_verified', 'is_sample']
    search_fields = ['title', ]
    filterset_fields = ['author', 'category', 'difficulty', 'course', 'event', 'is_verified', 'is_sample']
    pagination_class = BasePagination
