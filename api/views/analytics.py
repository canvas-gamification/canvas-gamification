from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from analytics.models.models import SubmissionAnalytics, QuestionAnalytics
from analytics.services.question_analytics import get_all_question_analytics, get_question_analytics
from analytics.services.submission_analytics import get_submission_analytics, get_all_submission_analytics
from api.permissions import TeacherAccessPermission
from course.models.models import Submission, Question


class AnalyticsViewSet(viewsets.GenericViewSet):
    permission_classes = [TeacherAccessPermission]
    queryset = SubmissionAnalytics.objects.all()

    def list(self, request):
        return Response(get_all_submission_analytics())

    @action(detail=False, methods=['get'], url_path='submission')
    def submission(self, request):
        submission_id = request.GET.get('id', None)
        print(submission_id)
        submission = get_object_or_404(Submission, pk=submission_id)
        return Response(get_submission_analytics(submission))


class QuestionAnalyticsViewSet(viewsets.GenericViewSet):
    permission_classes = [TeacherAccessPermission]
    queryset = QuestionAnalytics.objects.all()

    def list(self, request):
        return Response(get_all_question_analytics())

    @action(detail=False, methods=['get'], url_path='question')
    def question(self, request):
        question_id = request.GET.get('id', None)
        print(question_id)
        question = get_object_or_404(Question, pk=question_id)
        return Response(get_question_analytics(question))
