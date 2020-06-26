# Create your views here.
from rest_framework import viewsets

from api.permissions import TeacherAccessPermission
from api.serializers import QuestionSerializer, MultipleChoiceQuestionSerializer
from course.models.models import Question, MultipleChoiceQuestion


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class MultipleChoiceQuestionViewSet(viewsets.ModelViewSet):
    queryset = MultipleChoiceQuestion.objects.all()
    serializer_class = MultipleChoiceQuestionSerializer
    permission_classes = [TeacherAccessPermission, ]
