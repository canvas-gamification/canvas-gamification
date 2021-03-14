from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers.java_question import JavaSubmissionSerializer
from api.serializers.multiple_choice_question import MultipleChoiceSubmissionSerializer
from api.serializers.parsons_question import ParsonsSubmissionSerializer
from course.models.models import Submission, MultipleChoiceSubmission, JavaSubmission
from course.models.parsons_question import ParsonsSubmission


class SubmissionViewSet(viewsets.ViewSet):
    """
    Optional Parameters
    ?question: number => filter the submissions by question
    """
    permission_classes = [IsAuthenticated]

    def get_serialized_data(self, submission):
        if isinstance(submission, MultipleChoiceSubmission):
            return MultipleChoiceSubmissionSerializer(submission).data
        if isinstance(submission, JavaSubmission):
            return JavaSubmissionSerializer(submission).data
        if isinstance(submission, ParsonsSubmission):
            return ParsonsSubmissionSerializer(submission).data

    def list(self, request):
        question = request.GET.get("question", None)

        query_set = Submission.objects.filter(uqj__user=request.user)
        if question:
            query_set = query_set.filter(uqj__question_id=question)
        results = [
            self.get_serialized_data(submission) for submission in query_set
        ]
        return Response(results)

    def retrieve(self, request, pk=None):
        submission = get_object_or_404(Submission.objects.all(), pk=pk)
        if submission.uqj.user != request.user:
            raise PermissionDenied()
        return Response(self.get_serialized_data(submission))
