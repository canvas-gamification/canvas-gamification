from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

from canvas.models.models import Event, CanvasCourse, CanvasCourseRegistration, TA, INSTRUCTOR


def is_course_member(user, course):
    """
    True for teachers, the course instructor and anyone holding a VERIFIED
    registration. Unlike ``CanvasCourse.is_registered`` this never creates a
    registration row as a side effect.
    """
    if not user.is_authenticated:
        return False
    if user.is_teacher or course.instructor_id == user.id:
        return True
    return CanvasCourseRegistration.objects.filter(course=course, user=user, status="VERIFIED").exists()


def is_course_staff(user, course):
    """True for teachers, the course instructor, and TA/INSTRUCTOR registrations."""
    if not user.is_authenticated:
        return False
    if user.is_teacher or course.instructor_id == user.id:
        return True
    return CanvasCourseRegistration.objects.filter(
        course=course, user=user, registration_type__in=[TA, INSTRUCTOR]
    ).exists()


class TeacherAccessPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_teacher


class QuestionPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        if request.user.is_teacher:
            return True

        if request.method == "POST":
            event_id = request.data.get("event", None)
            event = Event.objects.filter(id=event_id).first()
            if not event:
                return False
            return event.has_edit_permission(request.user)

        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return obj.has_view_permission(request.user)
        return obj.has_edit_permission(request.user)


class UserConsentPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method in ["GET", "POST"]:
            return request.user == obj.user
        return False


class StudentsMustBeRegisteredPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        course = obj
        if user.is_student and not course.is_registered(user):
            return False
        return True


class GradeBookPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method == "GET":
            return obj.has_edit_permission(request.user)
        return True


class CoursePermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method == "POST":
            return True
        if request.method in ["PUT", "PATCH", "DELETE"]:
            return obj.has_edit_permission(request.user)
        if request.method == "GET":
            return True
            # TODO: this breaks the registrations
            # return obj.has_view_permission(request.user)
        return False


class EventCreatePermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.user.is_teacher:
            return True

        if request.method == "POST":
            course_id = request.data.get("course", None)
            type = request.data.get("type", None)
            course = CanvasCourse.objects.filter(id=course_id).first()
            if not course:
                return True
            if type == "CHALLENGE":
                return course.has_create_challenge_permission(request.user)
            return course.has_create_event_permission(request.user)
        return True

    def has_object_permission(self, request, view, obj):
        # Reached by the event detail actions (add-question-set, set-featured, ...).
        # Creation itself is checked in has_permission; acting on an existing
        # event needs edit rights on it.
        if request.method == "POST":
            return obj.has_edit_permission(request.user)
        return True


class EventEditPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in ["PUT", "PATCH", "DELETE"]:
            return obj.has_edit_permission(user)
        return True


class EventSetPermission(permissions.IsAuthenticated):
    """
    Creating an event set needs event-creation rights on its course (the same
    rule as creating an event); changing or deleting one needs edit rights on
    the event set itself. Reads stay open to any authenticated user.
    """

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method == "POST":
            return EventCreatePermission().has_permission(request, view)
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.has_edit_permission(request.user)


class HasDeletePermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE":
            return obj.author == request.user
        return True


class IsOwnerOrReadOnly(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.has_edit_permission(user)


class HasViewSubmissionPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return obj.has_view_permission(user)
        return True


class TeamPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in SAFE_METHODS:
            return is_course_member(user, obj.event.course)
        return obj.course_registrations.filter(user=user).exists()
