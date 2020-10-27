import re
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import Http404
from django.shortcuts import render, get_object_or_404

# Create your views here.
from canvas.models import CanvasCourse, Event
from canvas.utils.token_use import update_token_use, TokenUseException
from canvas.utils.utils import get_course_registration
from course.models.models import UserQuestionJunction
from course.views.views import teacher_check
from canvas.forms.forms import CreateEventForm


def course_list_view(request):
    courses = CanvasCourse.objects.all()
    if not request.user.is_authenticated or not request.user.is_teacher():
        courses.filter(visible_to_students=True)

    return render(request, 'canvas/course_list.html', {
        'courses': courses,
    })


def course_view(request, pk):
    course = get_object_or_404(CanvasCourse, pk=pk)

    if request.method == 'POST':
        token_use_data = {}
        for key in request.POST.keys():
            match = re.fullmatch(r"token_use#(\d+)", key)
            if match:
                token_use_option_id = int(match.group(1))
                token_use_num = int(request.POST.get(key, '0') or 0)
                token_use_data[token_use_option_id] = token_use_num
        try:
            update_token_use(request.user, course, token_use_data)
            messages.add_message(request, messages.SUCCESS, "Tokens Updated Successfully")
        except TokenUseException:
            messages.add_message(request, messages.ERROR, "Invalid Use of Tokens")

    is_instructor = course.is_instructor(request.user)
    if is_instructor:
        uqjs = UserQuestionJunction.objects.filter(user=request.user, question__course=course).all()
    else:
        uqjs = UserQuestionJunction.objects.none()

    course_reg = get_course_registration(request.user, course)

    return render(request, 'canvas/course.html', {
        'course': course,
        'course_reg': course_reg,
        'uqjs': uqjs,
        'is_instructor': is_instructor,
    })


def event_problem_set(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if not event.is_allowed_to_open(request.user):
        raise Http404()

    uqjs = UserQuestionJunction.objects.filter(user=request.user, question__event=event).all()

    return render(request, 'canvas/event_problem_set.html', {
        'event': event,
        'uqjs': uqjs,
        'is_instructor': event.course.is_instructor(request.user),
    })


@user_passes_test(teacher_check)
def events_options_view(request):
    course_id = request.GET.get('course_id', -1)
    course = get_object_or_404(CanvasCourse, pk=course_id)

    return render(request, 'canvas/course_event_options.html', {
        'events': course.events.all(),
    })


def create_event_view(request, pk):
    course = get_object_or_404(CanvasCourse, pk=pk)
    course.is_instructor(request.user)
    if request.method == 'POST':
        if course.is_instructor(request.user):
            form = CreateEventForm(request.POST)
            if form.is_valid():
                new_event = form.save(commit=False)
                new_event.course = course
                new_event.save()
                messages.add_message(request, messages.SUCCESS, 'Event created successfully.')
        else:
            messages.add_message(request, messages.ERROR,
                                 'You do not have permission to create an event in this course.')
    else:
        form = CreateEventForm()

    return render(request, 'canvas/event_create.html', {
        'form': form,
        'course': course,
    })
