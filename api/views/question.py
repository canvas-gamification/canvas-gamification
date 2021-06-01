from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters

from api.pagination import BasePagination
from api.permissions import TeacherAccessPermission, IsOwnerOrReadOnly
from api.serializers import QuestionSerializer, MultipleChoiceQuestionSerializer, JavaQuestionSerializer, \
    ParsonsQuestionSerializer
from course.models.models import Question, MultipleChoiceQuestion, JavaQuestion
from course.models.parsons_question import ParsonsQuestion


class QuestionViewSet(viewsets.ModelViewSet):
    """
    Optional Parameters
    ?status: boolean => filter by status
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsOwnerOrReadOnly, TeacherAccessPermission, ]
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
