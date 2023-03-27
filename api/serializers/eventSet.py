from rest_framework import serializers

from canvas.models.event_set import EventSet


class EventSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSet
        fields = [
            "name",
            "course",
            "event",
            "tokens",
        ]
