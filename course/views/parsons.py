from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy

from accounts.utils.decorators import show_login
from course.forms.parsons import ParsonsQuestionForm
from course.models.parsons_question import ParsonsSubmission


@show_login('You need to be logged in to create a question')
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


def parsons_question_view(request, question):
    def return_render():
        return render(request, 'parsons_question.html', {
            'question': question,
            'submissions': question.submissions.filter(
                user=request.user).all() if request.user.is_authenticated else ParsonsSubmission.objects.none(),
            'submission_class': ParsonsSubmission,
        })

    if request.method == "POST":

        code = request.POST.get("code", "")

        if not request.user.is_authenticated:
            messages.add_message(request, messages.ERROR, 'You need to be logged in to submit answers')
        elif not question.is_allowed_to_submit:
            messages.add_message(request, messages.ERROR, 'Maximum number of submissions reached')
        elif request.user.submissions.filter(question=question, code=code).exists():
            messages.add_message(request, messages.INFO, 'You have already submitted this answer!')
        else:
            submission = ParsonsSubmission()
            submission.user = request.user
            submission.code = code
            submission.question = question

            submission.submit()
            submission.save()

            messages.add_message(request, messages.INFO, "Your Code has been submitted and being evaluated!")

            return HttpResponseRedirect(reverse_lazy('course:question_view', kwargs={'pk': question.pk}))

    return return_render()


def parsons_submission_detail_view(request, submission):
    return render(request, 'parsons_submission_detail.html', {
        'submission': submission,
    })