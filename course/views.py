from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.template.defaultfilters import register

from course.forms import ProblemFilterForm, MultipleChoiceQuestionForm, CheckboxQuestionForm, \
    JavaQuestionForm
from course.models import Question, MultipleChoiceQuestion, Submission, CheckboxQuestion, JavaQuestion, JavaSubmission, \
    QuestionCategory, DIFFICULTY_CHOICES, TokenValue


# Create your views here.

def question_create_view(request, question_form_class):
    if request.method == 'POST':
        form = question_form_class(request.POST)

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
        form = question_form_class()

    return render(request, 'problem_create.html', {
        'form': form,
    })


def java_question_create_view(request):
    return question_create_view(request, JavaQuestionForm)


def multiple_choice_question_create_view(request):
    return question_create_view(request, MultipleChoiceQuestionForm)


def checkbox_question_create_view(request):
    return question_create_view(request, CheckboxQuestionForm)


def multiple_choice_question_view(request, question, template_name):
    if request.method == 'POST':

        answer = request.POST.get('answer', None)
        if not answer:
            answer = request.POST.getlist('answer[]')
        answer = str(answer)

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
                received_tokens = get_token_value(question.category, question.difficulty) * submission.grade
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

    return render(request, template_name, {
        'question': question,
        'statement': question.get_rendered_text(request.user),
        'choices': question.get_rendered_choices(request.user),
        'submissions': question.submissions.filter(
            user=request.user).all() if request.user.is_authenticated else Submission.objects.none(),
    })


def java_question_view(request, question):
    def return_render():
        return render(request, 'java_question.html', {
            'question': question,
            'submissions': question.java_submissions.filter(
                user=request.user).all() if request.user.is_authenticated else JavaSubmission.objects.none(),
        })

    if request.method == "POST":

        answer_text = request.POST.get('answer-text', "")
        answer_file = request.FILES.get('answer-file', None)

        answer_text = answer_text.strip()

        if answer_text == "" and not answer_file:
            messages.add_message(request, messages.ERROR, "Please either submit the code as text or upload a java file")
            return return_render()

        if answer_text != "" and answer_file:
            messages.add_message(request, messages.ERROR,
                                 "Both text and file was submitted please. Please only submit a text or a file")
            return return_render()

        if answer_file:
            answer_text = answer_file.read()

        if not request.user.is_authenticated:
            messages.add_message(request, messages.ERROR, 'You need to be logged in to submit answers')
        elif request.user.java_submissions.filter(question=question, code=answer_text).exists():
            messages.add_message(request, messages.INFO, 'You have already submitted this answer!')
        else:
            submission = JavaSubmission()
            submission.user = request.user
            submission.code = answer_text
            submission.question = question

            submission.submit()

            messages.add_message(request, messages.INFO, "Your Code has been submitted and being evaluated!")

    return return_render()


def question_view(request, pk):
    question = get_object_or_404(Question, pk=pk)

    if isinstance(question, JavaQuestion):
        return java_question_view(request, question)

    if isinstance(question, CheckboxQuestion):
        return multiple_choice_question_view(request, question, 'checkbox_question.html')

    if isinstance(question, MultipleChoiceQuestion):
        return multiple_choice_question_view(request, question, 'multiple_choice_question.html')

    raise Http404()


def get_token_value(category, difficulty):
    if not category or not difficulty:
        return 0

    if not TokenValue.objects.filter(category=category, difficulty=difficulty).exists():
        token_value = TokenValue(category=category, difficulty=difficulty)
        token_value.save()
        return token_value.value
    return TokenValue.objects.get(category=category, difficulty=difficulty).value


def problem_set_view(request):
    query = request.GET.get('query', None)
    difficulty = request.GET.get('difficulty', None)
    solved = request.GET.get('solved', None)
    category = request.GET.get('category', None)

    q = Q(is_verified=True)

    if query:
        q = q & Q(title__contains=query)
    if difficulty:
        q = q & Q(difficulty=difficulty)
    if category:
        q = q & Q(category=category)

    problems = Question.objects.filter(q).all()

    for problem in problems:
        problem.token_value = get_token_value(problem.category, problem.difficulty)

    if request.user.is_authenticated:
        for problem in problems:

            if isinstance(problem, JavaQuestion):
                problem.is_solved = JavaSubmission.objects.filter(question=problem, user=request.user, grade=1).exists()
                problem.is_partially_correct = not problem.is_solved and JavaSubmission.objects.filter(question=problem,
                                                                                                       user=request.user,
                                                                                                       grade__gt=0).exists()
                problem.no_submission = not JavaSubmission.objects.filter(question=problem, user=request.user).exists()
                problem.is_wrong = not problem.is_solved and not problem.no_submission and not problem.is_partially_correct
            else:
                problem.is_solved = Submission.objects.filter(question=problem, user=request.user,
                                                              is_correct=True).exists()
                problem.is_partially_correct = False
                problem.no_submission = not Submission.objects.filter(question=problem, user=request.user).exists()
                problem.is_wrong = not problem.is_solved and not problem.no_submission
    else:
        for problem in problems:
            problem.is_solved = False
            problem.is_partially_correct = False
            problem.no_submission = True
            problem.is_wrong = False

    if solved == 'Solved':
        problems = [p for p in problems if p.is_solved]
    if solved == 'Unsolved':
        problems = [p for p in problems if not p.is_solved]
    if solved == "Partially Correct":
        problems = [p for p in problems if p.is_partially_correct]
    if solved == 'Wrong':
        problems = [p for p in problems if p.is_wrong]
    if solved == 'Unopened':
        problems = [p for p in problems if p.no_submission]

    form = ProblemFilterForm(request.GET)

    return render(request, 'problem_set.html', {
        'problems': problems,
        'form': form,
    })


def java_submission_detail_view(request, pk):
    java_submission = get_object_or_404(JavaSubmission, pk=pk)

    if java_submission.user != request.user:
        raise Http404()

    return render(request, 'java_submission_detail.html', {
        'submission': java_submission,
    })


@register.filter
def return_item(l, i):
    try:
        return l[i]
    except:
        return None


def token_values_table_view(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    if request.method == 'POST':
        sent_values = request.POST.getlist('values[]', None)
        values = []

        for i, category in enumerate(QuestionCategory.objects.all()):
            values.append(sent_values[i * len(DIFFICULTY_CHOICES):(i + 1) * len(DIFFICULTY_CHOICES)])

            for j, difficulty in enumerate([x for x, y in DIFFICULTY_CHOICES]):
                token_value = TokenValue.objects.get(category=category, difficulty=difficulty)
                token_value.value = sent_values[i * len(DIFFICULTY_CHOICES) + j]
                token_value.save()
    else:
        values = []

        for category in QuestionCategory.objects.all():
            values.append([])

            for difficulty, x in DIFFICULTY_CHOICES:

                if TokenValue.objects.filter(category=category, difficulty=difficulty).exists():
                    token_value = TokenValue.objects.get(category=category, difficulty=difficulty)
                else:
                    token_value = TokenValue(category=category, difficulty=difficulty)
                    token_value.save()

                values[-1].append(token_value.value)

    return render(request, 'token_values_table.html', {
        'values': values,
        'difficulties': [d for d, x in DIFFICULTY_CHOICES],
        'categories': QuestionCategory.objects.all(),
    })
