from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers import CanvasCourseRegistrationSerializer
from canvas.models.models import CanvasCourseRegistration


class CanvasCourseRegistrationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Optional Parameters
    - Base filtering on the 'course' parameter
    """

    serializer_class = CanvasCourseRegistrationSerializer
    permission_classes = [
        IsAuthenticated,
    ]
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_fields = [
        "course",
    ]

    def get_queryset(self):
        user = self.request.user
        return CanvasCourseRegistration.objects.filter(user=user).all()

    @action(detail=True, methods=["get"], url_path="total-tokens-received")
    def total_tokens_received(self, request, pk):
        """
        Given course_reg id, Return all students for a course_reg
        """
        course_reg = get_object_or_404(CanvasCourseRegistration, id=pk)
        events = course_reg.course.events.filter(count_for_tokens=True, end_date__lt=timezone.now())
        tokens = 0

        for event in events:
            team = event.team_set.filter(course_registrations=course_reg).first()
            if team is None:
                tokens += 0
            else:
                tokens += event.tokens_received(team)

        return Response(tokens)
