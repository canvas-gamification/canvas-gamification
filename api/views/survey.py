from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.permissions import TeacherAccessPermission
from api.renderers import CSVRenderer
from api.serializers.survey import SurveySerializer
from canvas.models.models import CanvasCourse
from general.models.survey import Survey


class SurveyViewSet(viewsets.mixins.CreateModelMixin, viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_fields = [
        "code",
        "user",
    ]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            reports = Survey.objects.all()
        else:
            reports = Survey.objects.filter(user=user).all()
        return reports

    def perform_create(self, serializer):
        request = serializer.context["request"]
        code = request.data["code"]
        self.get_queryset().filter(code=code).delete()
        serializer.save(user=request.user)

    @action(detail=False, methods=["get"], url_path="check")
    def check_survey(self, request):
        courses = CanvasCourse.objects.filter(
            start_date__lt=timezone.now(),
            end_date__gt=timezone.now(),
            end_date__lt=timezone.now() + timezone.timedelta(weeks=4),
        ).all()

        has_final_survey = Survey.objects.filter(user=request.user, code="final").exists()
        has_initial_survey = Survey.objects.filter(user=request.user, code="initial").exists()

        # Comment out logic for survey check as it is not currently required

        # if not has_initial_survey:
        #     return Response({"code": "initial"})
        #
        # if has_final_survey:
        #     return Response({"code": None})

        # for course in courses:
        #     if course.is_registered(request.user):
        #         return Response({"code": "final"})

        return Response({"code": None})


class ExportSurveyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [TeacherAccessPermission]
    renderer_classes = [CSVRenderer]

    filter_backends = [filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend]
    ordering_fields = [
        "time_created",
    ]
    filterset_fields = {
        "user": ["exact"],
        "user__role": ["exact"],
        "time_created": ["range", "lt", "gt"],
        "code": ["exact"],
    }
    search_fields = ["response"]

    @property
    def default_response_headers(self):
        headers = super().default_response_headers
        headers["Content-Disposition"] = 'attachment; filename="surveys.csv"'
        return headers
