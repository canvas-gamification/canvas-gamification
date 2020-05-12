from django.shortcuts import render

# Create your views here.
from django.utils.decorators import classonlymethod
from rest_framework import viewsets

from api.serializers import QuestionSerializer
from course.models import Question


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    @classonlymethod
    def as_view(cls, actions=None, **initkwargs):
        return super().as_view({'get': 'list'})

