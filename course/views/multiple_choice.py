from django.contrib import messages
from django.forms import formset_factory
from django.shortcuts import render

from course.exceptions import SubmissionException
from course.forms.multiple_choice import MultipleChoiceQuestionForm, ChoiceForm
from course.models.multiple_choice import MultipleChoiceSubmission
from course.utils.utils import create_multiple_choice_question, QuestionCreateException, get_user_question_junction, \
    get_question_title


def _multiple_choice_question_create_view(request, header, question_form_class, correct_answer_formset_class,
                                          distractor_answer_formset_class):
    if request.method == 'POST':
        correct_answer_formset = correct_answer_formset_class(request.POST, prefix='correct')
        distractor_answer_formset = distractor_answer_formset_class(request.POST, prefix='distractor')
        form = question_form_class(request.user, request.POST)

        if correct_answer_formset.is_valid() and distractor_answer_formset.is_valid() and form.is_valid():

            try:
                create_multiple_choice_question(
                    title=form.cleaned_data['title'],
                    text=form.cleaned_data['text'],
                    author=request.user,
                    category=form.cleaned_data['category'],
                    difficulty=form.cleaned_data['difficulty'],
                    variables=form.cleaned_data['variables'],
                    visible_distractor_count=form.cleaned_data['visible_distractor_count'],
                    answer_text=correct_answer_formset.forms[0].cleaned_data['text'],
                    distractors=[form.cleaned_data['text'] for form in distractor_answer_formset.forms if
                                 not form.cleaned_data['DELETE']],
                    course=form.cleaned_data['course'],
                    event=form.cleaned_data['event'],
                )
                messages.add_message(request, messages.SUCCESS, 'Problem was created successfully')
                form = question_form_class(request.user)
                correct_answer_formset = correct_answer_formset_class(prefix='correct')
                distractor_answer_formset = distractor_answer_formset_class(prefix='distractor')

            except QuestionCreateException as e:
                messages.add_message(request, messages.ERROR, e.user_message)
    else:
        form = question_form_class(request.user)

        correct_answer_formset = correct_answer_formset_class(prefix='correct')
        distractor_answer_formset = distractor_answer_formset_class(prefix='distractor')

    return render(request, 'problem_create.html', {
        'form': form,
        'correct_answer_formset': correct_answer_formset,
        'distractor_answer_formset': distractor_answer_formset,
        'header': header,
    })


def _multiple_choice_question_view(request, question, template_name, key):
    if request.method == 'POST':

        answer = request.POST.get('answer', None)
        if not answer:
            answer = request.POST.getlist('answer[]')
        answer = str(answer)

        try:
            submission = submit_solution(question, request.user, answer)

            if question.is_exam:
                messages.add_message(request, messages.INFO, 'Your submission was received.')
            elif submission.is_correct:
                received_tokens = get_user_question_junction(request.user, question).tokens_received
                messages.add_message(
                    request, messages.SUCCESS,
                    'Answer submitted. Your answer was correct. You received {} tokens'.format(
                        round(received_tokens, 2)),
                )
            else:
                messages.add_message(
                    request, messages.ERROR,
                    'Answer submitted. Your answer was wrong',
                )

        except SubmissionException as e:
            messages.add_message(request, messages.ERROR, "{}".format(e))

    return render(request, template_name, {
        'question': question,
        'uqj': get_user_question_junction(request.user, question),
        'submission_class': MultipleChoiceSubmission,
        'title': get_question_title(request.user, question, key)
    })


def _multiple_choice_question_edit_view(request, question):
    correct_answer_formset_class = formset_factory(ChoiceForm, extra=1, can_delete=True, max_num=1, min_num=1)
    distractor_answer_formset_class = formset_factory(ChoiceForm, extra=0, can_delete=True)

    if request.method == 'POST':
        correct_answer_formset = correct_answer_formset_class(request.POST, prefix='correct')
        distractor_answer_formset = distractor_answer_formset_class(request.POST, prefix='distractor')
        form = MultipleChoiceQuestionForm(request.user, request.POST)

        if correct_answer_formset.is_valid() and distractor_answer_formset.is_valid() and form.is_valid():
            try:
                create_multiple_choice_question(
                    pk=question.pk,
                    title=form.cleaned_data['title'],
                    text=form.cleaned_data['text'],
                    max_submission_allowed=question.max_submission_allowed,
                    author=question.author,
                    category=form.cleaned_data['category'],
                    difficulty=form.cleaned_data['difficulty'],
                    is_verified=question.is_verified,
                    variables=form.cleaned_data['variables'],
                    visible_distractor_count=form.cleaned_data['visible_distractor_count'],
                    answer_text=correct_answer_formset.forms[0].cleaned_data['text'],
                    distractors=[form.cleaned_data['text'] for form in distractor_answer_formset.forms if
                                 not form.cleaned_data['DELETE']],
                    course=form.cleaned_data['course'],
                    event=form.cleaned_data['event'],
                )
                messages.add_message(request, messages.SUCCESS, 'Problem saved successfully')
            except QuestionCreateException as e:
                messages.add_message(request, messages.ERROR, e.user_message)

    else:
        form = MultipleChoiceQuestionForm(request.user, instance=question)

        correct_answer_formset = correct_answer_formset_class(
            prefix='correct',
            initial=[{'text': question.choices[question.answer]}]
        )
        distractor_answer_formset = distractor_answer_formset_class(
            prefix='distractor',
            initial=[{'text': value} for name, value in question.choices.items() if name != question.answer]
        )

    return render(request, 'problem_create.html', {
        'form': form,
        'correct_answer_formset': correct_answer_formset,
        'distractor_answer_formset': distractor_answer_formset,
        'header': 'Edit Question',
    })


def submit_solution(question, user, solution):
    uqj = get_user_question_junction(user, question)

    if not user.is_teacher and uqj.submissions.filter(answer=solution).exists():
        raise SubmissionException("You have already submitted this answer!")

    if not uqj.is_allowed_to_submit:
        raise SubmissionException("You are not allowed to submit")

    submission = MultipleChoiceSubmission()
    submission.answer = solution
    submission.uqj = uqj

    submission.submit()
    submission.save()
    uqj.save()

    return submission
