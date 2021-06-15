from django.contrib import admin
from leader_board.models import Leader_Board



class LeaderBoardAdmin(admin.ModelAdmin):
    list_display = ('__str__','userId','courseId','total_tokens_received','leaderBoardId',)
    list_filter = ('userId','courseId','total_tokens_received', 'leaderBoardId',)


# Register your models here.
admin.site.register(Leader_Board, LeaderBoardAdmin)