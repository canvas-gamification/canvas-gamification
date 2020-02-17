from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.urls import reverse_lazy
from django.views.generic import CreateView

from course.forms import ProblemCreateForm
from course.models import Question, MultipleChoiceQuestion, Submission


class ProblemCreateView(CreateView):
    model = Question
    form_class = ProblemCreateForm
    template_name = 'problem_create.html'
    success_url = reverse_lazy('course:new_problem')


def multiple_choice_question_view(request, pk):
    question = get_object_or_404(MultipleChoiceQuestion, pk=pk)

    if request.method == 'POST':
        answer = request.POST.get('answer', None)

        submission = Submission()
        submission.user = request.user
        submission.answer = answer
        submission.problem = question

        submission.save()

    return render(request, 'multiple_choice_question.html', {
        'question': question,
        'submissions': Submission.objects.filter(user=request.user).filter(
            content_type=ContentType.objects.get_for_model(MultipleChoiceQuestion)).filter(
            object_id=pk).all(),
    })
