from canvas.models.models import CanvasCourse


def get_registered_students(course: CanvasCourse):
    stu_info = [{course_reg.id, course_reg.name} for course_reg in course.canvascourseregistration_set.all()]
    return stu_info
