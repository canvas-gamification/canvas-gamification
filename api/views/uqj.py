from django.db.models import Q
from django_filters import NumberFilter, ChoiceFilter, Filter, BooleanFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from course.models.models import UserQuestionJunction, Question, DIFFICULTY_CHOICES
from api.pagination import BasePagination
from api.serializers import UQJSerializer


class UQJCategoryParentFilter(Filter):
    def filter(self, qs, value):
        if not value:
            return qs

        return qs.filter(
            Q(question__category__parent=value) | Q(question__category__parent__isnull=True, question__category=value)
        )


class UQJFilterSet(FilterSet):
    question_event = NumberFilter(field_name='question__event')
    question = NumberFilter(field_name='question')
    difficulty = ChoiceFilter(field_name='question__difficulty', choices=DIFFICULTY_CHOICES)
    category = NumberFilter(field_name='question__category')
    parent_category = UQJCategoryParentFilter()
    is_verified = BooleanFilter(field_name='question__is_verified')
    is_practice = BooleanFilter(field_name='question__event', lookup_expr='isnull')

    class Meta:
        model = UserQuestionJunction
        fields = ['question', 'question_event', 'difficulty', 'category', 'is_solved', 'is_verified', 'is_practice']


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
