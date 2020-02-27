from django.http import Http404
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


def multiple_choice_question_view(request, question):
    if request.method == 'POST':
        answer = request.POST.get('answer', None)

        submission = Submission()
        submission.user = request.user
        submission.answer = answer
        submission.question = question

        submission.save()

    return render(request, 'multiple_choice_question.html', {
        'question': question,
        'statement': question.get_rendered_text(request.user),
        'choices': question.get_rendered_choices(request.user),
        'submissions': question.submissions.filter(user=request.user).all() if request.user.is_authenticated else Submission.objects.none(),
    })


def question_view(request, pk):
    question = get_object_or_404(Question, pk=pk)

    if isinstance(question, MultipleChoiceQuestion):
        return multiple_choice_question_view(request, question)

    raise Http404()


def problem_set_view(request):
    problems = Question.objects.all()

    if request.user.is_authenticated:
        for problem in problems:
            problem.is_solved = Submission.objects.filter(question=problem, user=request.user, is_correct=True).exists()
            problem.no_submission = not Submission.objects.filter(question=problem, user=request.user).exists()
            problem.is_wrong = not problem.is_solved and not problem.no_submission

    return render(request, 'problem_set.html', {
        'problems': problems,
    })
