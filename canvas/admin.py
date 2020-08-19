from django.contrib import admin

# Register your models here.
from canvas.models import CanvasCourse, CanvasCourseRegistration

admin.site.register(CanvasCourse)
admin.site.register(CanvasCourseRegistration)