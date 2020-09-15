from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404

# Create your views here.
from canvas.models import CanvasCourse, CanvasCourseRegistration, Event
from course.models.models import UserQuestionJunction
from course.views.views import teacher_check


def course_list_view(request):
    courses = CanvasCourse.objects.all()
    if not request.user.is_authenticated or not request.user.is_teacher():
        courses.filter(visible_to_students=True)

    return render(request, 'canvas/course_list.html', {
        'courses': courses,
    })


def course_view(request, pk):
    course = get_object_or_404(CanvasCourse, pk=pk)

    qs = CanvasCourseRegistration.objects.filter(user=request.user, course=course)
    course_reg = qs.get() if qs.exists() else None

    return render(request, 'canvas/course.html', {
        'course': course,
        'course_reg': course_reg
    })


def event_problem_set(request, event_id):

    event = get_object_or_404(Event, pk=event_id)
    if not event.is_allowed_to_open(request.user):
        raise Http404()

    uqjs = UserQuestionJunction.objects.filter(user=request.user, question__event=event).all()

    return render(request, 'canvas/event_problem_set.html', {
        'event': event,
        'uqjs': uqjs,
    })

