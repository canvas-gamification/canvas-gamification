from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import api.error_messages as ERROR_MESSAGES
from api.permissions import HasViewSubmissionPermission
from api.serializers import (
    JavaSubmissionSerializer,
    MultipleChoiceSubmissionSerializer,
    ParsonsSubmissionSerializer,
)
from api.serializers.java_question import (
    JavaSubmissionHiddenDetailsSerializer,
)
from api.serializers.multiple_choice_question import (
    MultipleChoiceSubmissionHiddenDetailsSerializer,
)
from api.serializers.parsons_question import (
    ParsonsSubmissionHiddenDetailsSerializer,
)
from canvas.models.models import EVENT_TYPE_CHOICES
from course.exceptions import SubmissionException
from course.models.java import JavaQuestion, JavaSubmission
from course.models.models import Submission, Question, UserQuestionJunction
from course.models.multiple_choice import (
    MultipleChoiceQuestion,
    MultipleChoiceSubmission,
)
from course.models.parsons import ParsonsSubmission, ParsonsQuestion
from course.services.submission import (
    submit_java_solution,
    submit_mcq_solution,
    submit_parsons_solution,
)
from general.services.action import create_submission_action, team_complete_challenge_action


class SubmissionViewSet(viewsets.GenericViewSet):
    """
    Optional Parameters
    ?question: number => filter the submissions by question
    """

    permission_classes = [
        IsAuthenticated,
        HasViewSubmissionPermission,
    ]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = [
        "submission_time",
    ]
    queryset = Submission.objects.all()
    serializer_class = MultipleChoiceSubmissionSerializer

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
        question_id = request.GET.get("question", None)
        question = get_object_or_404(Question, id=question_id)
        query_set = self.filter_queryset(self.get_queryset())

        team = None
        if not question.is_practice:
            teams = question.event.team_set.filter(course_registrations__user=request.user).all()
            team = None if len(teams) == 0 else teams[0]

        if not request.user.is_teacher:
            if team is None:
                query_set = query_set.filter(uqj__user=request.user)
            else:
                users = [course_reg.user for course_reg in team.course_registrations.all()]
                query_set = query_set.filter(uqj__user__in=users)

        if question_id:
            query_set = query_set.filter(uqj__question_id=question_id)

        results = [self.get_serialized_data(submission) for submission in query_set]
        return Response(results)

    def retrieve(self, request, pk=None):
        submission = get_object_or_404(Submission.objects.all(), pk=pk)
        return Response(self.get_serialized_data(submission))

    @action(detail=False, methods=["post"])
    def submit(self, request):
        question_id = request.data.get("question", None)
        solution = request.data.get("solution", None)

        if question_id is None or solution is None:
            raise ValidationError(ERROR_MESSAGES.SUBMISSION.INVALID)

        question = get_object_or_404(Question, pk=question_id)

        try:
            if isinstance(question, MultipleChoiceQuestion):
                submission = submit_mcq_solution(question, request.user, solution)
            elif isinstance(question, JavaQuestion):
                submission = submit_java_solution(question, request.user, solution)
            elif isinstance(question, ParsonsQuestion):
                submission = submit_parsons_solution(question, request.user, solution)
            else:
                raise ValidationError(ERROR_MESSAGES.QUESTION.INVALID)
        except SubmissionException as e:
            raise ValidationError("{}".format(e))

        create_submission_action(submission)

        if question.event.type == EVENT_TYPE_CHOICES.CHALLENGE:
            course = question.course
            course_reg = course.canvascourseregistration_set.filter(user=request.user)

            event = question.event
            team = event.team_set.filter(course_registrations__contains=[course_reg])

            if team.course_registrations_set.count() > 1:
                users = [course_reg.user for course_reg in team.course_registrations.all()]
                solved_uqjs = UserQuestionJunction.objects.all().filter(user__in=users, is_solved=True)
                solved_event_question_id = [
                    solved_uqj.question.id
                    for solved_uqj in solved_uqjs
                    if solved_uqj.question.event.id is question.event.id
                ]

                solved_event_question_id = list(set(solved_event_question_id))
                event_question_ids = [ele['id'] for ele in event.question_set.values_list('id')]

                if len(event_question_ids) is len(solved_event_question_id):
                    team_complete_challenge_action(question.event.id, team, request.user)


        return Response(
            self.get_serialized_data(submission),
            status=status.HTTP_201_CREATED,
        )
