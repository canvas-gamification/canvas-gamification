from django_filters import NumberFilter
from rest_framework import viewsets, filters
from analytics.models import SubmissionAnalytics, QuestionAnalytics
from api.pagination import BasePagination
from api.permissions import TeacherAccessPermission
from api.serializers.submission_analytics import SubmissionAnalyticsSerializer, QuestionAnalyticsSerializer
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
    filter_backends = [DjangoFilterBackend,]


class QuestionAnalyticsFilterSet(FilterSet):
    question_event = NumberFilter(field_name='question__event')
    question = NumberFilter(field_name='question')

    class Meta:
        model = QuestionAnalytics
        fields = ['question', 'question_event']


class QuestionAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuestionAnalytics.objects.all()
    serializer_class = QuestionAnalyticsSerializer
    permission_classes = [TeacherAccessPermission]
    pagination_class = BasePagination
    filter_class = QuestionAnalyticsFilterSet
    filter_backends = [DjangoFilterBackend,]


# class EventAnalyticsFilterSet(FilterSet):
#     question_event = NumberFilter(field_name='question__event')
#
#     class Meta:
#         model = EventAnalytics
#         fields = ['question_event']
#
#
# class EventAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = EventAnalytics.objects.all()
#     serializer_class = EventAnalyticsSerializer
#     permission_classes = [TeacherAccessPermission]
#     pagination_class = BasePagination
#     filter_class = EventAnalyticsFilterSet
#     filter_backends = [DjangoFilterBackend,]