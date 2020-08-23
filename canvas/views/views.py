from django.shortcuts import render

# Create your views here.
from canvas.models import CanvasCourse


def course_list_view(request):
    courses = CanvasCourse.objects.all()
    if not request.user.is_authenticated or not request.user.is_teacher():
        courses.filter(visible_to_students=True)

    return render(request, 'canvas/course_list.html', {
        'courses': courses,
    })


def course_view(request, pk):
    return render(request, 'canvas/course.html')


