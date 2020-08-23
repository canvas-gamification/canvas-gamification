from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from rest_framework.reverse import reverse_lazy

from canvas.models import CanvasCourse, CanvasCourseRegistration


def name_registration_view(request, course, course_reg):
    if request.method == "POST":
        if 'name' in request.POST:
            name = request.POST.get("name", "")
            guessed_name = course.guess_user(name)
            if guessed_name is None:
                return render(request, 'canvas/course_registration.html', {
                    'name': name,
                    'failed': True,
                })

            return render(request, 'canvas/course_registration.html', {
                'guessed_name': guessed_name[0],
            })
        elif 'confirmed_name' in request.POST:
            canvas_user = course.get_user(name=request.POST.get('confirmed_name', ''))
            if not canvas_user:
                return HttpResponseBadRequest()
            course_reg.canvas_user_id = canvas_user.id
            course_reg.save()
            return HttpResponseRedirect(reverse_lazy('canvas:course_register', kwargs={'pk': course.pk}))

    return render(request, 'canvas/course_registration.html', {
        'name': True,
    })


def verify_registration_view(request, course, course_reg):
    if request.method == "POST":
        code = request.POST.get('code', -1)
        valid = course_reg.check_verification_code(code)
        if valid:
            return render(request, 'canvas/course_registration.html', {
                'success': True,
            })
        else:
            return render(request, 'canvas/course_registration.html', {
                'verification_failed': True,
                'verification': True,
                'attempts': course_reg.verification_attempts,
            })
    course_reg.send_verification_code()
    return render(request, 'canvas/course_registration.html', {
        'verification': True,
        'attempts': course_reg.verification_attempts,
    })


@login_required
def register_course_view(request, pk):
    course = get_object_or_404(CanvasCourse, pk=pk)

    qs = CanvasCourseRegistration.objects.filter(user=request.user, course=course)

    if qs.exists():
        course_reg = qs.get()
    else:
        course_reg = CanvasCourseRegistration(user=request.user, course=course)
        course_reg.save()

    if course_reg.is_blocked:
        return render(request, 'canvas/course_registration.html', {
            'blocked': True,
        })

    if not course_reg.canvas_user_id:
        return name_registration_view(request, course, course_reg)

    if not course_reg.is_verified:
        return verify_registration_view(request, course, course_reg)

    return render(request, 'canvas/course_registration.html', {
        'success': True,
    })
