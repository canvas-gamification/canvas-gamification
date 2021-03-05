from rest_framework import permissions


class TeacherAccessPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_teacher


class QuestionAccessPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        authenticated = bool(request.user and request.user.is_authenticated)
        teacher = authenticated and request.user.is_teacher
        safe = request.method in permissions.SAFE_METHODS
        return teacher or (safe and authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.has_view_permission(request.user)
        else:
            return obj.has_edit_permission(request.user)


class UserConsentPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if 'user' not in request.data:
            return True
        try:
            return int(request.data['user']) == request.user.id
        except Exception:
            return False

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user
