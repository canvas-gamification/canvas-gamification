from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from api.serializers import JavaSubmissionSerializer, MultipleChoiceSubmissionSerializer, ParsonsSubmissionSerializer
from course.exceptions import SubmissionException
from course.models.models import Submission, MultipleChoiceSubmission, JavaSubmission, Question, \
    MultipleChoiceQuestion, JavaQuestion
from course.models.parsons_question import ParsonsSubmission, ParsonsQuestion
from course.views.java import submit_solution as submit_java_solution
from course.views.multiple_choice import submit_solution as submit_multiple_choice_solution
from course.views.parsons import submit_solution as submit_parsons_solution


class SubmissionViewSet(viewsets.ViewSet):
    """
    Optional Parameters
    ?question: number => filter the submissions by question
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['submission_time', ]

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

    @action(detail=False, methods=['post'])
    def submit(self, request):
        question_id = request.data.get("question", None)
        solution = request.data.get("solution", None)

        if question_id is None or solution is None:
            raise ValidationError("Parameters question and solution should be provided.")

        question = get_object_or_404(Question, pk=question_id)

        try:
            if isinstance(question, MultipleChoiceQuestion):
                submission = submit_multiple_choice_solution(question, request.user, solution)
            elif isinstance(question, JavaQuestion):
                submission = submit_java_solution(question, request.user, solution)
            elif isinstance(question, ParsonsQuestion):
                submission = submit_parsons_solution(question, request.user, solution)
            else:
                raise ValidationError("Incorrect question format.")
        except SubmissionException as e:
            raise ValidationError("{}".format(e))

        return Response(self.get_serialized_data(submission))
