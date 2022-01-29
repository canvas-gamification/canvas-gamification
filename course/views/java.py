import json

from django.contrib import messages
from django.shortcuts import render

from course.exceptions import SubmissionException
from course.forms.java import JavaQuestionForm
from course.models.java import JavaSubmission
from course.utils.utils import get_user_question_junction, get_question_title


def _java_question_create_view(request, header, question_form_class):
    if request.method == 'POST':
        form = question_form_class(request.user, request.POST)

        if form.is_valid():
            question = form.save()
            question.author = request.user
            question.is_verified = request.user.is_teacher
            question.save()

            messages.add_message(request, messages.SUCCESS, 'Question was created successfully')

            form = question_form_class(request.user)
    else:
        form = question_form_class(request.user)

    return render(request, 'problem_create.html', {
        'form': form,
        'header': header,
    })


def _java_question_edit_view(request, question):
    if request.method == 'POST':
        form = JavaQuestionForm(request.user, request.POST, instance=question)

        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Question was edited successfully')
    else:
        form = JavaQuestionForm(request.user, instance=question)

    return render(request, 'problem_create.html', {
        'form': form,
        'header': "Edit Question",
    })


def _java_question_view(request, question, key):
    def return_render():
        return render(request, 'java_question.html', {
            'question': question,
            'uqj': get_user_question_junction(request.user, question),
            'submission_class': JavaSubmission,
            'title': get_question_title(request.user, question, key)
        })

    if request.method == "POST":

        file_names = question.get_input_file_names_array()
        answer_dict = {}
        for file_name in file_names:
            if file_name not in request.POST:
                messages.add_message(request, messages.ERROR, "{} is required".format(file_name))
                return return_render()
            answer_dict[file_name] = request.POST[file_name]

        try:
            submit_solution(question, request.user, answer_dict)
            messages.add_message(request, messages.INFO,
                                 "Your Code has been submitted and is being evaluated! Refresh page to view results.")
        except SubmissionException as e:
            messages.add_message(request, messages.ERROR, "{}".format(e))

    return return_render()


def _java_submission_detail_view(request, submission):
    return render(request, 'code_submission_detail.html', {
        'submission': submission,
    })


def submit_solution(question, user, answer_dict):

    if isinstance(answer_dict, str):
        answer_dict = json.loads(answer_dict)

    uqj = get_user_question_junction(user, question)

    if not uqj.is_allowed_to_submit:
        raise SubmissionException("You are not allowed to submit")

    submission = JavaSubmission()
    submission.answer_files = answer_dict
    submission.uqj = uqj

    submission.submit()
    submission.save()
    uqj.save()

    return submission
