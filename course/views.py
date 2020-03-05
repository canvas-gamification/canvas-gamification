from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, get_object_or_404

from course.forms import ProblemCreateForm, ProblemFilterForm
from course.models import Question, MultipleChoiceQuestion, Submission


# Create your views here.


def multiple_choice_question_create_view(request):
    if request.method == 'POST':
        form = ProblemCreateForm(request.POST)

        if not request.user.is_authenticated:
            messages.add_message(request, messages.ERROR, 'You need to be logged in to create a question')
        elif form.is_valid():
            question = form.save(commit=False)
            question.user = request.user
            question.is_verified = request.user.is_teacher()
            question.save()

            messages.add_message(request, messages.SUCCESS, 'Problem was created successfully')

    else:
        if not request.user.is_authenticated:
            messages.add_message(request, messages.ERROR, 'You need to be logged in to create a question')
        form = ProblemCreateForm()

    return render(request, 'problem_create.html', {
        'form': form,
    })


def multiple_choice_question_view(request, question):
    if request.method == 'POST':
        answer = request.POST.get('answer', None)

        if not request.user.is_authenticated:
            messages.add_message(request, messages.ERROR, 'You need to be logged in to submit answers')
        elif request.user.submissions.filter(question=question, answer=answer).exists():
            messages.add_message(request, messages.INFO, 'You have already submitted this answer!')
        else:
            submission = Submission()
            submission.user = request.user
            submission.answer = answer
            submission.question = question

            submission.save()

            if submission.is_correct:
                received_tokens = question.token_value * submission.grade
                request.user.tokens += received_tokens
                request.user.save()
                messages.add_message(
                    request, messages.SUCCESS,
                    'Answer submitted. Your answer was correct. You received {} tokens'.format(received_tokens),
                )
            else:
                messages.add_message(
                    request, messages.ERROR,
                    'Answer submitted. Your answer was wrong',
                )

    return render(request, 'multiple_choice_question.html', {
        'question': question,
        'statement': question.get_rendered_text(request.user),
        'choices': question.get_rendered_choices(request.user),
        'submissions': question.submissions.filter(
            user=request.user).all() if request.user.is_authenticated else Submission.objects.none(),
    })


def question_view(request, pk):
    question = get_object_or_404(Question, pk=pk)

    if isinstance(question, MultipleChoiceQuestion):
        return multiple_choice_question_view(request, question)

    raise Http404()


def problem_set_view(request):
    query = request.GET.get('query', None)
    difficulty = request.GET.get('difficulty', None)
    solved = request.GET.get('solved', 'All')

    q = Q(is_verified=True)

    if query:
        q = q & Q(title__contains=query)
    if difficulty and difficulty != 'All':
        q = q & Q(difficulty=difficulty)

    problems = Question.objects.filter(q).all()

    if request.user.is_authenticated:
        for problem in problems:
            problem.is_solved = Submission.objects.filter(question=problem, user=request.user, is_correct=True).exists()
            problem.no_submission = not Submission.objects.filter(question=problem, user=request.user).exists()
            problem.is_wrong = not problem.is_solved and not problem.no_submission
    else:
        for problem in problems:
            problem.no_submission = True

    if solved == 'Solved':
        problems = [p for p in problems if p.is_solved]
    if solved == 'Unsolved':
        problems = [p for p in problems if not p.is_solved]
    if solved == 'Wrong':
        problems = [p for p in problems if p.is_wrong]
    if solved == 'Unopened':
        problems = [p for p in problems if p.no_submission]

    form = ProblemFilterForm(request.GET)

    return render(request, 'problem_set.html', {
        'problems': problems,
        'form': form,
    })
