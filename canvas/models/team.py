from django.db import models

from canvas.models.models import Event, CanvasCourseRegistration


class Team(models.Model):
    time_created = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)
    is_private = models.BooleanField(default=False)
    who_can_join = models.ManyToManyField(CanvasCourseRegistration)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    course_registrations = models.ManyToManyField(CanvasCourseRegistration)