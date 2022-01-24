from django_filters import NumberFilter, ChoiceFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from course.models.models import UserQuestionJunction, Question, DIFFICULTY_CHOICES
from api.pagination import BasePagination
from api.serializers import UQJSerializer


class UQJFilterSet(FilterSet):
    question_event = NumberFilter(field_name='question__event')
    question = NumberFilter(field_name='question')
    difficulty = ChoiceFilter(field_name='question__difficulty', choices=DIFFICULTY_CHOICES)
    category = NumberFilter(field_name='question__category')

    class Meta:
        model = UserQuestionJunction
        fields = ['question', 'question_event', 'difficulty', 'category', 'is_solved']


class UQJViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Query Parameters
    + Standard ordering is applied on the field 'last_viewed'
    """
    serializer_class = UQJSerializer
    permission_classes = [IsAuthenticated, ]
    pagination_class = BasePagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, ]
    ordering_fields = ['last_viewed', ]
    filter_class = UQJFilterSet

    def get_queryset(self):
        user = self.request.user
        uqj = user.question_junctions.filter(question__question_status=Question.CREATED)
        accessible_uqj = []
        for temp in uqj:
            if temp.question.has_view_permission(user):
                accessible_uqj.append(temp.question)
        uqj = user.question_junctions.filter(question__in=accessible_uqj)
        return uqj
