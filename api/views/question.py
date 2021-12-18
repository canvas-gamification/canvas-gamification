from collections import OrderedDict

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.pagination import BasePagination
from api.permissions import TeacherAccessPermission, HasDeletePermission
from api.serializers import QuestionSerializer, MultipleChoiceQuestionSerializer, JavaQuestionSerializer, \
    ParsonsQuestionSerializer
from course.models.models import Question, UserQuestionJunction
from course.models.java import JavaQuestion
from course.models.multiple_choice import MultipleChoiceQuestion
from course.models.parsons import ParsonsQuestion
from general.services.action import delete_question_action


class QuestionViewSet(viewsets.ModelViewSet):
    """
    Optional Parameters
    ?status: boolean => filter by status
    """
    queryset = Question.objects.filter(question_status=Question.CREATED)
    serializer_class = QuestionSerializer
    permission_classes = [HasDeletePermission, TeacherAccessPermission, ]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend]
    ordering_fields = ['id', 'title', 'author', 'difficulty', 'event__name', 'category__name', 'category__parent__name']
    search_fields = ['title', ]
    filterset_fields = ['author', 'difficulty', 'course', 'event', 'is_verified', 'is_sample', 'category__name',
                        'category__parent__name']
    pagination_class = BasePagination

    def get_question_serializer_class(self, question):
        if isinstance(question, MultipleChoiceQuestion):
            return MultipleChoiceQuestionSerializer
        if isinstance(question, JavaQuestion):
            return JavaQuestionSerializer
        if isinstance(question, ParsonsQuestion):
            return ParsonsQuestionSerializer
        return self.get_serializer_class()

    def get_serializer(self, *args, **kwargs):
        question = kwargs.get('instance', None)
        if not question and len(args) == 1:
            question = args[0]

        if question:
            serializer_class = self.get_question_serializer_class(question)
        else:
            serializer_class = self.get_serializer_class()

        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        question = self.get_object()
        question.question_status = Question.DELETED
        question.save()
        delete_question_action(self.get_serializer(question).data, request.user)
        return Response(self.get_serializer(question).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='download-questions')
    def download_questions(self, request, *args, **kwargs):
        '''
        Action that will display all questions after they have been filtered using the appropriate constructors,
        ready to put into a JSON file to download and export.
        '''
        queryset = self.filter_queryset(self.get_queryset())
        serialized_questions = []
        for obj in queryset:
            serialized_questions.append(OrderedDict(self.get_serializer(obj).data))
        return Response(serialized_questions)

    @action(detail=True, methods=['get'], url_path='count-favorite')
    def get_favorite_count(self, request, pk=None):

        uqj_count = UserQuestionJunction.objects.all().filter(question_id=pk, is_favorite=True).count()
        return Response(uqj_count)
