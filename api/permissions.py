from rest_framework import permissions


class TeacherAccessPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_teacher()


class UserConsentPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if 'user' not in request.data:
            return True
        try:
            return int(request.data['user']) == request.user.id
        except Exception:
            return False
