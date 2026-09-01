from api.filters import DjangoFilterBackend
from rest_framework import viewsets

from api.permissions import EventSetPermission
from api.serializers.eventSet import EventSetSerializer
from canvas.models.models import EventSet


class EventSetViewSet(viewsets.ModelViewSet):
    serializer_class = EventSetSerializer
    permission_classes = [EventSetPermission]
    queryset = EventSet.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["events"]
