from django.contrib import messages
from django.shortcuts import render

from course.exceptions import SubmissionException
from course.forms.java import JavaQuestionForm
from course.models.models import JavaSubmission
from course.utils.submissions import submit_solution
from course.utils.utils import get_user_question_junction


def _java_question_create_view(request, header, question_form_class):
    if request.method == 'POST':
        form = question_form_class(request.user, request.POST)

        if form.is_valid():
            question = form.save()
            question.author = request.user
            question.is_verified = request.user.is_teacher()
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
        form = JavaQuestionForm(request.user, request.POST)

        if form.is_valid():
            edited_question = form.save()
            edited_question.pk = question.pk
            edited_question.id = question.id
            edited_question.is_verified = request.user.is_teacher()
            edited_question.save()

            messages.add_message(request, messages.SUCCESS, 'Question was edited successfully')
    else:
        form = JavaQuestionForm(request.user, instance=question)

    return render(request, 'problem_create.html', {
        'form': form,
        'header': "Edit Question",
    })


def _java_question_view(request, question):
    def return_render():
        return render(request, 'java_question.html', {
            'question': question,
            'uqj': get_user_question_junction(request.user, question),
            'submission_class': JavaSubmission,
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
            answer_text = answer_file.read().decode("ascii", "ignore")

        try:
            submit_solution(question, request.user, answer_text)
            messages.add_message(request, messages.INFO, "Your Code has been submitted and being evaluated!")
        except SubmissionException as e:
            messages.add_message(request, messages.ERROR, "{}".format(e))

    return return_render()


def _java_submission_detail_view(request, submission):
    return render(request, 'java_submission_detail.html', {
        'submission': submission,
    })
