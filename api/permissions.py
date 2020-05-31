from rest_framework import permissions


class TeacherAccessPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_teacher()
