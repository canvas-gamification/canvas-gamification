from django.contrib import admin

# Register your models here.
from canvas.models import CanvasCourse, CanvasCourseRegistration, Event, TokenUseOption, TokenUse

admin.site.register(CanvasCourse)
admin.site.register(CanvasCourseRegistration)
admin.site.register(Event)
admin.site.register(TokenUseOption)
admin.site.register(TokenUse)
