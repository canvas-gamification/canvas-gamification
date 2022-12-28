from django.contrib import admin

# Register your models here.
from canvas.models.models import (
    CanvasCourse,
    CanvasCourseRegistration,
    Event,
    TokenUseOption,
    TokenUse,
)
from canvas.models.team import Team
from canvas.models.goal import Goal, GoalItem

admin.site.register(CanvasCourse)
admin.site.register(CanvasCourseRegistration)
admin.site.register(Event)
admin.site.register(TokenUseOption)
admin.site.register(TokenUse)
admin.site.register(Team)
admin.site.register(Goal)
admin.site.register(GoalItem)
