from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from analytics.models.models import SubmissionAnalytics
from analytics.services.submission_analytics import get_submission_analytics, get_all_submission_analytics
from api.permissions import TeacherAccessPermission
from course.models.models import Submission


class AnalyticsViewSet(viewsets.GenericViewSet):
    permission_classes = [TeacherAccessPermission]
    queryset = SubmissionAnalytics.objects.all()

    def list(self, request):
        return Response(get_all_submission_analytics())

    @action(detail=False, methods=['get'])
    def submission(self, request):
        submission_id = request.GET.get('submission', None)
        submission = get_object_or_404(Submission, pk=submission_id)
        return Response(get_submission_analytics(submission))
