from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

# Create your views here.
from canvas.models import CanvasCourse, CanvasCourseRegistration, Event
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

    is_instructor = course.is_instructor(request.user)
    if is_instructor:
        uqjs = UserQuestionJunction.objects.filter(user=request.user, question__course=course).all()
    else:
        uqjs = UserQuestionJunction.objects.none()

    qs = CanvasCourseRegistration.objects.filter(user=request.user, course=course)
    course_reg = qs.get() if qs.exists() else None

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

def create_event_view(request):
    if request.method == 'POST':
        form = CreateEventForm(request.POST)
        if form.is_valid():
            name = form.cleand_data['name']
            course = form.cleand_data['course']
            count_for_tokens = form.cleand_data['count_for_tokens']
            start_dt = form.cleand_data['start_datetime']
            end_dt = form.cleand_data['end_datetime']

            try:
                new_event = Event(name, course, count_for_tokens, start_dt, end_dt)
                new_event.save()
                messages.add_message(request, messages.SUCCESS, 'Event created successfully')
            except:
                messages.add_message(request, messages.ERROR, 'Error in event creation.')
            # redirect to a new URL:
            return HttpResponseRedirect('.')

            # if a GET (or any other method) we'll create a blank form
    else:
        form = CreateEventForm()

    return render(request, 'canvas/event_create.html', {
        'form': form,
    })