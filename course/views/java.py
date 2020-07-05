from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy

from course.forms.java import JavaQuestionForm
from course.models.models import JavaSubmission


def _java_question_create_view(request, header, question_form_class):
    if request.method == 'POST':
        form = question_form_class(request.POST)

        if form.is_valid():
            question = form.save()
            question.author = request.user
            question.is_verified = request.user.is_teacher()
            question.save()

            messages.add_message(request, messages.SUCCESS, 'Question was created successfully')

            form = question_form_class()
    else:
        form = question_form_class()

    return render(request, 'problem_create.html', {
        'form': form,
        'header': header,
    })


def _java_question_edit_view(request, question):
    if request.method == 'POST':
        form = JavaQuestionForm(request.POST)

        if form.is_valid():
            edited_question = form.save()
            edited_question.pk = question.pk
            edited_question.id = question.id
            edited_question.is_verified = request.user.is_teacher()
            edited_question.save()

            messages.add_message(request, messages.SUCCESS, 'Question was edited successfully')
    else:
        form = JavaQuestionForm(instance=question)

    return render(request, 'problem_create.html', {
        'form': form,
        'header': "Edit Question",
    })


def _java_question_view(request, question):
    def return_render():
        return render(request, 'java_question.html', {
            'question': question,
            'submissions': question.submissions.filter(
                user=request.user).all() if request.user.is_authenticated else JavaSubmission.objects.none(),
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

        if not request.user.is_authenticated:
            messages.add_message(request, messages.ERROR, 'You need to be logged in to submit answers')
        elif not question.is_allowed_to_submit:
            messages.add_message(request, messages.ERROR, 'Maximum number of submissions reached')
        elif request.user.submissions.filter(question=question, code=answer_text).exists():
            messages.add_message(request, messages.INFO, 'You have already submitted this answer!')
        else:
            submission = JavaSubmission()
            submission.user = request.user
            submission.code = answer_text
            submission.question = question

            submission.submit()
            submission.save()

            messages.add_message(request, messages.INFO, "Your Code has been submitted and being evaluated!")

            return HttpResponseRedirect(reverse_lazy('course:question_view', kwargs={'pk': question.pk}))

    return return_render()


def _java_submission_detail_view(request, submission):
    return render(request, 'java_submission_detail.html', {
        'submission': submission,
    })
