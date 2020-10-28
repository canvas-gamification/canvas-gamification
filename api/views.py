# Create your views here.
from rest_framework import viewsets, mixins

from api.permissions import TeacherAccessPermission
from api.serializers import QuestionSerializer, MultipleChoiceQuestionSerializer, UserConsentSerializer
from course.models.models import Question, MultipleChoiceQuestion


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [TeacherAccessPermission, ]


class SampleMultipleChoiceQuestionViewSet(viewsets.ModelViewSet):
    queryset = MultipleChoiceQuestion.objects.filter(is_sample=True).all()
    serializer_class = MultipleChoiceQuestionSerializer


class UserConsentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserConsentSerializer
