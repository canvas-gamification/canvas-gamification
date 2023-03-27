from django.db import models

from canvas.models.models import Event, CanvasCourse


class EventSet(models.Model):
    name = models.CharField(max_length=500)
    course = models.ForeignKey(CanvasCourse, related_name="eventSets", on_delete=models.CASCADE)
    event = models.ManyToManyField(Event, related_name="eventSets", blank=True, on_delete=models.SET_NULL)
    tokens = models.FloatField()
