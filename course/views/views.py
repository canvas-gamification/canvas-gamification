from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q, Count
from django.forms import formset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from rest_framework.reverse import reverse_lazy

from accounts.utils.decorators import show_login
from course.forms.forms import ProblemFilterForm
from course.forms.java import JavaQuestionForm
from course.forms.multiple_choice import CheckboxQuestionForm, MultipleChoiceQuestionForm, ChoiceForm
from course.models.models import Question, MultipleChoiceQuestion, CheckboxQuestion, JavaQuestion, JavaSubmission, \
    QuestionCategory, DIFFICULTY_CHOICES, TokenValue, Submission, UserQuestionJunction
from course.models.parsons_question import ParsonsQuestion, ParsonsSubmission
from course.utils.utils import get_token_value, get_user_question_junction
from course.views.java import _java_question_create_view, _java_question_view, _java_submission_detail_view, \
    _java_question_edit_view
from course.views.multiple_choice import _multiple_choice_question_create_view, _multiple_choice_question_view, \
    _multiple_choice_question_edit_view
from course.views.parsons import _parsons_question_create_view, _parsons_question_view, _parsons_submission_detail_view, \
    _parsons_question_edit_view


def teacher_check(user):
    return not user.is_anonymous and user.is_teacher()


@user_passes_test(teacher_check)
def multiple_choice_question_create_view(request):
    return _multiple_choice_question_create_view(
        request,
        'New Multiple Choice Question',
        MultipleChoiceQuestionForm,
        formset_factory(ChoiceForm, extra=1, can_delete=True, max_num=1, min_num=1),
        formset_factory(ChoiceForm, extra=2, can_delete=True),
    )


@user_passes_test(teacher_check)
def checkbox_question_create_view(request):
    return _multiple_choice_question_create_view(
        request,
        'New Checkbox Question',
        CheckboxQuestionForm,
        formset_factory(ChoiceForm, extra=1, can_delete=True),
        formset_factory(ChoiceForm, extra=2, can_delete=True),
    )


@user_passes_test(teacher_check)
def java_question_create_view(request):
    return _java_question_create_view(request, 'New Java Question', JavaQuestionForm)


@user_passes_test(teacher_check)
def parsons_question_create_view(request):
    return _parsons_question_create_view(request, 'New Parsons Question')


@show_login('You need to be logged in to submit an answer')
def question_view(request, pk):
    question = get_object_or_404(Question, pk=pk)

    uqj = get_user_question_junction(request.user, question)
    uqj.viewed()

    if isinstance(question, JavaQuestion):
        return _java_question_view(request, question)

    if isinstance(question, CheckboxQuestion):
        return _multiple_choice_question_view(request, question, 'checkbox_question.html')

    if isinstance(question, MultipleChoiceQuestion):
        return _multiple_choice_question_view(request, question, 'multiple_choice_question.html')

    if isinstance(question, ParsonsQuestion):
        return _parsons_question_view(request, question)

    raise Http404()


@user_passes_test(teacher_check)
def question_edit_view(request, pk):
    question = get_object_or_404(Question, pk=pk)

    if isinstance(question, MultipleChoiceQuestion):
        return _multiple_choice_question_edit_view(request, question)

    if isinstance(question, JavaQuestion):
        return _java_question_edit_view(request, question)

    if isinstance(question, ParsonsQuestion):
        return _parsons_question_edit_view(request, question)

    raise Http404()


@user_passes_test(teacher_check)
def question_delete_view(request, pk):
    question = get_object_or_404(Question, pk=pk)

    if question.author != request.user:
        messages.add_message(request, messages.ERROR,
                             'Unauthorized request to delete question. '
                             'Please ask the author to delete.')
    else:
        question.delete()

    return HttpResponseRedirect(reverse_lazy('course:problem_set'))


def problem_set_view(request):
    query = request.GET.get('query', None)
    difficulty = request.GET.get('difficulty', None)
    solved = request.GET.get('solved', None)
    category = request.GET.get('category', None)

    q = Q(question__is_verified=True)

    if query:
        q = q & Q(question__title__contains=query)
    if difficulty:
        q = q & Q(question__difficulty=difficulty)
    if category:
        q = q & (Q(question__category=category) | Q(question__category__parent=category))

    if solved == 'Solved':
        q = q & Q(is_solved=True)
    if solved == 'Unsolved':
        q = q & Q(is_solved=False, is_partially_solved=False)
    if solved == "Partially Correct":
        q = q & Q(is_partially_solved=True)
    if solved == 'Wrong':
        q = q & Q(submissions__count__gt=0, is_solved=False,
                  is_partially_solved=False)
    if solved == 'New':
        q = q & Q(submissions__count=0, last_viewed__isnull=True)

    if request.user.is_authenticated:
        uqjs = request.user.question_junctions.annotate(Count('submissions')).filter(q).all()
    else:
        uqjs = UserQuestionJunction.objects.none()

    form = ProblemFilterForm(request.GET)

    return render(request, 'problem_set.html', {
        'uqjs': uqjs,
        'form': form,
        'header': 'problem_set',
    })


def submission_detail_view(request, pk):
    submission = get_object_or_404(Submission, pk=pk)

    if submission.user != request.user:
        raise Http404()

    if isinstance(submission, JavaSubmission):
        return _java_submission_detail_view(request, submission)
    if isinstance(submission, ParsonsSubmission):
        return _parsons_submission_detail_view(request, submission)
    raise Http404()


@user_passes_test(teacher_check)
def token_values_table_view(request):
    query_set = QuestionCategory.objects.filter(parent__isnull=False).all()

    if request.method == 'POST':
        sent_values = request.POST.getlist('values[]', None)
        values = []

        for i, category in enumerate(query_set):
            values.append(sent_values[i * len(DIFFICULTY_CHOICES):(i + 1) * len(DIFFICULTY_CHOICES)])

            for j, difficulty in enumerate([x for x, y in DIFFICULTY_CHOICES]):
                token_value = TokenValue.objects.get(category=category, difficulty=difficulty)
                token_value.value = sent_values[i * len(DIFFICULTY_CHOICES) + j]
                token_value.save()
    else:
        values = []

        for category in query_set:
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
        'difficulties': [x for d, x in DIFFICULTY_CHOICES],
        'categories': query_set,
        'header': 'token_values',
    })
