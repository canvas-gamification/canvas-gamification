from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404

# Create your views here.
from canvas.models import CanvasCourse
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
    return render(request, 'canvas/course.html', {
        'course': course,
    })


