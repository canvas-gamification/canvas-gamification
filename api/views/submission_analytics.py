from django_filters import NumberFilter
from rest_framework import viewsets
from analytics.models.models import SubmissionAnalytics
from api.pagination import BasePagination
from api.permissions import TeacherAccessPermission
from api.serializers.submission_analytics import SubmissionAnalyticsSerializer
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
