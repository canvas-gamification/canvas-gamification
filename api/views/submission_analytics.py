from django_filters import NumberFilter
from rest_framework import viewsets

from analytics.models import JavaSubmissionAnalytics, MCQSubmissionAnalytics, ParsonsSubmissionAnalytics
from analytics.models.models import SubmissionAnalytics
from api.pagination import BasePagination
from api.permissions import TeacherAccessPermission
from api.serializers.submission_analytics import SubmissionAnalyticsSerializer, JavaSubmissionAnalyticsSerializer, \
    MCQSubmissionAnalyticsSerializer, ParsonsSubmissionAnalyticsSerializer
from django_filters.rest_framework import DjangoFilterBackend, FilterSet


class SubmissionAnalyticsFilterSet(FilterSet):
    question_event = NumberFilter(field_name='question__event')
    question = NumberFilter(field_name='question')

    class Meta:
        model = SubmissionAnalytics
        fields = ['question', 'question_event']


class SubmissionAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubmissionAnalytics.objects.all()
    serializer_class = SubmissionAnalyticsSerializer
    permission_classes = [TeacherAccessPermission]
    pagination_class = BasePagination
    filter_class = SubmissionAnalyticsFilterSet
    filter_backends = [DjangoFilterBackend, ]


class JavaSubmissionAnalyticsFilterSet(FilterSet):
    question_event = NumberFilter(field_name='question__event')
    question = NumberFilter(field_name='question')

    class Meta:
        model = JavaSubmissionAnalytics
        fields = ['question', 'question_event']


class JavaSubmissionAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JavaSubmissionAnalytics.objects.all()
    serializer_class = JavaSubmissionAnalyticsSerializer
    permission_classes = [TeacherAccessPermission]
    pagination_class = BasePagination
    filter_class = JavaSubmissionAnalyticsFilterSet
    filter_backends = [DjangoFilterBackend, ]


class MCQSubmissionAnalyticsFilterSet(FilterSet):
    question_event = NumberFilter(field_name='question__event')
    question = NumberFilter(field_name='question')

    class Meta:
        model = MCQSubmissionAnalytics
        fields = ['question', 'question_event']


class MCQSubmissionAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MCQSubmissionAnalytics.objects.all()
    serializer_class = MCQSubmissionAnalyticsSerializer
    permission_classes = [TeacherAccessPermission]
    pagination_class = BasePagination
    filter_class = MCQSubmissionAnalyticsFilterSet
    filter_backends = [DjangoFilterBackend, ]


class ParsonsSubmissionAnalyticsFilterSet(FilterSet):
    question_event = NumberFilter(field_name='question__event')
    question = NumberFilter(field_name='question')

    class Meta:
        model = ParsonsSubmissionAnalytics
        fields = ['question', 'question_event']


class ParsonsSubmissionAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParsonsSubmissionAnalytics.objects.all()
    serializer_class = ParsonsSubmissionAnalyticsSerializer
    permission_classes = [TeacherAccessPermission]
    pagination_class = BasePagination
    filter_class = ParsonsSubmissionAnalyticsFilterSet
    filter_backends = [DjangoFilterBackend, ]