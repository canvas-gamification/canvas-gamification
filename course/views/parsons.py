from django.contrib import messages
from django.shortcuts import render

from course.exceptions import SubmissionException
from course.forms.parsons import ParsonsQuestionForm
from course.models.parsons import ParsonsSubmission
from course.utils.utils import get_user_question_junction, get_question_title


def _parsons_question_create_view(request, header):
    if request.method == 'POST':
        form = ParsonsQuestionForm(request.user, request.POST)

        if form.is_valid():
            question = form.save()
            question.author = request.user
            question.is_verified = request.user.is_teacher
            question.save()

            messages.add_message(request, messages.SUCCESS, 'Question was created successfully')

            form = ParsonsQuestionForm(request.user)
    else:
        form = ParsonsQuestionForm(request.user)

    return render(request, 'problem_create.html', {
        'form': form,
        'header': header,
    })


def _parsons_question_edit_view(request, question):
    if request.method == 'POST':
        form = ParsonsQuestionForm(request.user, request.POST)

        if form.is_valid():
            edited_question = form.save()
            edited_question.pk = question.pk
            edited_question.id = question.id
            edited_question.is_verified = request.user.is_teacher
            edited_question.save()

            messages.add_message(request, messages.SUCCESS, 'Question was edited successfully')
    else:
        form = ParsonsQuestionForm(request.user, instance=question)

    return render(request, 'problem_create.html', {
        'form': form,
        'header': "Edit Question",
    })


def _parsons_question_view(request, question, key):
    def return_render():
        return render(request, 'parsons_question.html', {
            'question': question,
            'uqj': get_user_question_junction(request.user, question),
            'submission_class': ParsonsSubmission,
            'title': get_question_title(request.user, question, key)
        })

    if request.method == "POST":

        code = request.POST.get("code", "")

        try:
            submit_solution(question, request.user, code)
            messages.add_message(request, messages.INFO,
                                 "Your code has been submitted and is being evaluated! Refresh page to view results.")
        except SubmissionException as e:
            messages.add_message(request, messages.ERROR, "{}".format(e))

    return return_render()


def _parsons_submission_detail_view(request, submission):
    return render(request, 'code_submission_detail.html', {
        'submission': submission,
    })


def submit_solution(question, user, solution):
    uqj = get_user_question_junction(user, question)

    if not uqj.is_allowed_to_submit:
        raise SubmissionException("You are not allowed to submit")

    submission = ParsonsSubmission()
    submission.answer_files = solution
    submission.uqj = uqj

    submission.submit()
    submission.save()
    uqj.save()

    return submission
