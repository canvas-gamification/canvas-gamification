from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render

from canvas.models import CanvasCourse, CanvasCourseRegistration
from canvas.utils.utils import get_course_registration


def _student_number_registration_view(request, course, course_reg):
    student_number = request.POST.get("student_number", None)
    if student_number is not None:
        canvas_user = course.get_user(student_id=student_number)
        if canvas_user is None:
            messages.add_message(
                request,
                messages.ERROR,
                'No matching record found. Please make sure your id is correct.'
            )
            return render(request, 'canvas/course_registration/student_number_input.html', {
                'student_number': student_number
            })
        else:
            course_reg.set_canvas_user(canvas_user)
            return _verify_registration_view(request, course, course_reg)
    else:
        return render(request, 'canvas/course_registration/student_number_input.html')


def _name_registration_view(request, course, course_reg):
    if request.method == "POST":
        if 'student_number' in request.POST:
            return _student_number_registration_view(request, course, course_reg)
        elif 'name' in request.POST:
            name = request.POST.get("name", "")
            guessed_names = course.guess_user(name)
            if len(guessed_names) == 0:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'No matching record found. Please make sure your name is spelled correctly.'
                )
                return render(request, 'canvas/course_registration/name_input.html', {
                    'name': name
                })
            elif len(guessed_names) > 1:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'Multiple students with this name exist. Please enter your student number to '
                    'confirm your identity.'
                )
                return _student_number_registration_view(request, course, course_reg)
            return render(request, 'canvas/course_registration/name_confirm.html', {
                'guessed_name': guessed_names[0],
            })
        elif 'confirmed_name' in request.POST:
            canvas_user = course.get_user(name=request.POST.get('confirmed_name', ''))
            if not canvas_user:
                return HttpResponseBadRequest()
            course_reg.set_canvas_user(canvas_user)
            return _verify_registration_view(request, course, course_reg)
    return render(request, 'canvas/course_registration/name_input.html')


def _verify_registration_view(request, course, course_reg):
    code = request.POST.get('code', None)
    if code is not None:
        valid = course_reg.check_verification_code(code)
        if valid:
            messages.add_message(
                request,
                messages.SUCCESS,
                'You have successfully registered.'
            )
            return render(request, 'canvas/course_registration/empty.html', {
                'course': course,
            })
        else:
            messages.add_message(
                request,
                messages.ERROR,
                'Verification Failed.'
            )
            return render(request, 'canvas/course_registration/verification.html', {
                'attempts': course_reg.verification_attempts,
            })
    course_reg.send_verification_code()
    return render(request, 'canvas/course_registration/verification.html', {
        'attempts': course_reg.verification_attempts,
    })


@login_required
def register_course_view(request, pk):
    course = get_object_or_404(CanvasCourse, pk=pk)

    course_reg = get_course_registration(request.user, course)

    if course_reg is None:
        course_reg = CanvasCourseRegistration(user=request.user, course=course)
        course_reg.save()

    if course_reg.is_blocked:
        messages.add_message(
            request,
            messages.ERROR,
            'Registration has been blocked for you. Please contact your instructor.'
        )
        return render(request, 'canvas/course_registration/empty.html')

    if not course_reg.canvas_user_id:
        return _name_registration_view(request, course, course_reg)

    if not course_reg.is_verified:
        return _verify_registration_view(request, course, course_reg)

    messages.add_message(request, messages.SUCCESS, 'You are already registered.')
    return render(request, 'canvas/course_registration/empty.html', {
        'course': course,
    })
