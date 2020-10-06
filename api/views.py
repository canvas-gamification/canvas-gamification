# Create your views here.
from django.http import Http404, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, mixins

from api.permissions import TeacherAccessPermission
from api.serializers import QuestionSerializer, MultipleChoiceQuestionSerializer, UserConsentSerializer
from course.models.models import Question, MultipleChoiceQuestion


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [TeacherAccessPermission, ]


class MultipleChoiceQuestionViewSet(viewsets.ModelViewSet):
    queryset = MultipleChoiceQuestion.objects.all()
    serializer_class = MultipleChoiceQuestionSerializer
    permission_classes = [TeacherAccessPermission, ]


class UserConsentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserConsentSerializer
