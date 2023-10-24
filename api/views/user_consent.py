from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, filters
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserConsent
from api.permissions import UserConsentPermission, TeacherAccessPermission
from api.renderers import CSVRenderer
from api.serializers import UserConsentSerializer
from general.services.action import (
    give_user_consent_action,
    remove_user_consent_action,
)


class UserConsentViewSet(viewsets.ModelViewSet):
    queryset = UserConsent.objects.all()
    serializer_class = UserConsentSerializer
    permission_classes = [IsAuthenticated, UserConsentPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            return UserConsent.objects.all()
        return UserConsent.objects.filter(user=user)

    def perform_create(self, serializer):
        request = serializer.context["request"]
        serializer.save(user=request.user)
        if request.data["consent"]:
            user = request.user
            user.first_name = request.data["legal_first_name"]
            user.last_name = request.data["legal_last_name"]
            user.save()
            give_user_consent_action(request.user, request.data)
        else:
            remove_user_consent_action(request.user, request.data)


class ExportUserConsentViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = UserConsent.objects.all()
    serializer_class = UserConsentSerializer
    permission_classes = [TeacherAccessPermission]
    renderer_classes = [CSVRenderer]

    filter_backends = [filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend]
    ordering_fields = [
        "created_at",
    ]
    filterset_fields = {
        "user": ["exact"],
        "user__role": ["exact"],
        "created_at": ["range", "lt", "gt"],
        "consent": ["exact"],
        "access_submitted_course_work": ["exact"],
        "access_course_grades": ["exact"],
        "legal_first_name": ["exact"],
        "legal_last_name": ["exact"],
        "gender": ["exact"],
        "race": ["exact"],
        "student_number": ["exact"],
    }
    search_fields = ["legal_first_name", "legal_last_name"]

    @property
    def default_response_headers(self):
        headers = super().default_response_headers
        headers["Content-Disposition"] = 'attachment; filename="consents.csv"'
        return headers
