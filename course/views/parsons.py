from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy

from course.exceptions import SubmissionException
from course.forms.parsons import ParsonsQuestionForm
from course.models.parsons_question import ParsonsSubmission
from course.utils.submissions import submit_solution
from course.utils.utils import get_user_question_junction


def _parsons_question_create_view(request, header):
    if request.method == 'POST':
        form = ParsonsQuestionForm(request.POST)

        if form.is_valid():
            question = form.save()
            question.author = request.user
            question.is_verified = request.user.is_teacher()
            question.save()

            messages.add_message(request, messages.SUCCESS, 'Question was created successfully')

            form = ParsonsQuestionForm()
    else:
        form = ParsonsQuestionForm()

    return render(request, 'problem_create.html', {
        'form': form,
        'header': header,
    })


def _parsons_question_edit_view(request, question):
    if request.method == 'POST':
        form = ParsonsQuestionForm(request.POST)

        if form.is_valid():
            edited_question = form.save()
            edited_question.pk = question.pk
            edited_question.id = question.id
            edited_question.is_verified = request.user.is_teacher()
            edited_question.save()

            messages.add_message(request, messages.SUCCESS, 'Question was edited successfully')
    else:
        form = ParsonsQuestionForm(instance=question)

    return render(request, 'problem_create.html', {
        'form': form,
        'header': "Edit Question",
    })


def _parsons_question_view(request, question):
    def return_render():
        return render(request, 'parsons_question.html', {
            'question': question,
            'uqj': get_user_question_junction(request.user, question),
            'submission_class': ParsonsSubmission,
        })

    if request.method == "POST":

        code = request.POST.get("code", "")

        try:
            submission = submit_solution(question, request.user, code)
            messages.add_message(request, messages.INFO, "Your Code has been submitted and being evaluated!")
        except SubmissionException as e:
            messages.add_message(request, messages.ERROR, "{}".format(e))

    return return_render()


def _parsons_submission_detail_view(request, submission):
    return render(request, 'parsons_submission_detail.html', {
        'submission': submission,
    })
