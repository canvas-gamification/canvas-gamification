

def get_course_registration(user, course):
    from canvas.models import CanvasCourseRegistration

    qs = CanvasCourseRegistration.objects.filter(user=user, course=course)
    return qs.get() if qs.exists() else None
