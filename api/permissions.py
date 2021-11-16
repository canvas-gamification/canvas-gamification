from rest_framework import permissions


class TeacherAccessPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_teacher


class UserConsentPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'POST']:
            return request.user == obj.user
        return False


class StudentsMustBeRegisteredPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        course = obj
        if user.is_student and not course.is_registered(user):
            return False
        return True


class CourseEditPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method == "PUT":
            return obj.has_edit_permission(obj, request.user)
        return True


class CourseCreatePermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method == "POST":
            return request.user.is_teacher
        return True


class EventCreatePermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method == "POST":
            return obj.has_create_permission(user)
        return True


class EventEditPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method == "PUT":
            return obj.has_edit_permission(user)
        return True


class HasDeletePermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return obj.author == request.user
        return True


class IsOwnerOrReadOnly(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.has_edit_permission(user)
