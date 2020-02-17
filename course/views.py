from django.shortcuts import render

# Create your views here.
from django.urls import reverse_lazy
from django.views.generic import CreateView

from course.forms import ProblemCreateForm
from course.models import Question


class ProblemCreateView(CreateView):
    model = Question
    form_class = ProblemCreateForm
    template_name = 'problem_create.html'
    success_url = reverse_lazy('course:new_problem')
