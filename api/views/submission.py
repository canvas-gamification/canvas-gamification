from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import api.error_messages as ERROR_MESSAGES
from api.permissions import HasViewSubmissionPermission
from api.serializers import JavaSubmissionSerializer, MultipleChoiceSubmissionSerializer, ParsonsSubmissionSerializer
from api.serializers.java_question import JavaSubmissionHiddenDetailsSerializer
from api.serializers.multiple_choice_question import MultipleChoiceSubmissionHiddenDetailsSerializer
from api.serializers.parsons_question import ParsonsSubmissionHiddenDetailsSerializer
from course.exceptions import SubmissionException
from course.models.java import JavaQuestion, JavaSubmission
from course.models.models import Submission, Question
from course.models.multiple_choice import MultipleChoiceQuestion, MultipleChoiceSubmission
from course.models.parsons import ParsonsSubmission, ParsonsQuestion
from course.views.java import submit_solution as submit_java_solution
from course.views.multiple_choice import submit_solution as submit_multiple_choice_solution
from course.views.parsons import submit_solution as submit_parsons_solution
from general.services.action import create_submission_action


class SubmissionViewSet(viewsets.GenericViewSet):
    """
    Optional Parameters
    ?question: number => filter the submissions by question
    """
    permission_classes = [IsAuthenticated, HasViewSubmissionPermission, ]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['submission_time', ]
    queryset = Submission.objects.all()

    def get_serialized_data(self, submission):
        if submission.question.is_exam_and_open:
            if isinstance(submission, MultipleChoiceSubmission):
                return MultipleChoiceSubmissionHiddenDetailsSerializer(submission).data
            if isinstance(submission, JavaSubmission):
                return JavaSubmissionHiddenDetailsSerializer(submission).data
            if isinstance(submission, ParsonsSubmission):
                return ParsonsSubmissionHiddenDetailsSerializer(submission).data
        else:
            if isinstance(submission, MultipleChoiceSubmission):
                return MultipleChoiceSubmissionSerializer(submission).data
            if isinstance(submission, JavaSubmission):
                return JavaSubmissionSerializer(submission).data
            if isinstance(submission, ParsonsSubmission):
                return ParsonsSubmissionSerializer(submission).data

    def list(self, request):
        question = request.GET.get("question", None)

        if request.user.is_teacher:
            query_set = self.get_queryset()
        else:
            query_set = self.filter_queryset(self.get_queryset()).filter(uqj__user=request.user)
        if question:
            query_set = query_set.filter(uqj__question_id=question)

        results = [
            self.get_serialized_data(submission) for submission in query_set
        ]
        return Response(results)

    def retrieve(self, request, pk=None):
        submission = get_object_or_404(Submission.objects.all(), pk=pk)
        return Response(self.get_serialized_data(submission))

    @action(detail=False, methods=['post'])
    def submit(self, request):
        question_id = request.data.get("question", None)
        solution = request.data.get("solution", None)

        if question_id is None or solution is None:
            raise ValidationError(ERROR_MESSAGES.SUBMISSION.INVALID)

        question = get_object_or_404(Question, pk=question_id)

        try:
            if isinstance(question, MultipleChoiceQuestion):
                submission = submit_multiple_choice_solution(question, request.user, solution)
            elif isinstance(question, JavaQuestion):
                submission = submit_java_solution(question, request.user, solution)
            elif isinstance(question, ParsonsQuestion):
                submission = submit_parsons_solution(question, request.user, solution)
            else:
                raise ValidationError(ERROR_MESSAGES.QUESTION.INVALID)
        except SubmissionException as e:
            raise ValidationError("{}".format(e))

        create_submission_action(submission)
        return Response(self.get_serialized_data(submission), status=status.HTTP_201_CREATED)
