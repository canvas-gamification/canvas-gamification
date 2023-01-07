from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from api.serializers.survey import SurveySerializer
from general.models.survey import Survey


class SurveyViewSet(viewsets.mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        request = serializer.context["request"]
        serializer.save(user=request.user)
