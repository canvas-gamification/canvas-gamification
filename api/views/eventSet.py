from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from api.permissions import EventCreatePermission, EventEditPermission
from api.serializers.eventSet import EventSetSerializer
from canvas.models.models import EventSet


class EventSetViewSet(viewsets.ModelViewSet):
    serializer_class = EventSetSerializer
    permission_classes = [
        IsAuthenticated,
        EventCreatePermission,
        EventEditPermission,
    ]
    queryset = EventSet.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["events"]
