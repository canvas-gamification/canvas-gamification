from django.contrib import admin

# Register your models here.
from canvas.models import CanvasCourse, CanvasCourseRegistration, Event, TokenUseOption, TokenUse, Team

admin.site.register(CanvasCourse)
admin.site.register(CanvasCourseRegistration)
admin.site.register(Event)
admin.site.register(TokenUseOption)
admin.site.register(TokenUse)
admin.site.register(Team)
