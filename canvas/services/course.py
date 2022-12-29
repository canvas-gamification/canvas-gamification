from canvas.utils.utils import get_course_registration


def register_instructor(user, course):
    course_reg = get_course_registration(user, course)
    course_reg.set_instructor()
    course_reg.verify()
    course_reg.save()
