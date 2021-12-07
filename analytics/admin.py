from django.contrib import admin
from analytics.models import SubmissionAnalytics, QuestionAnalytics

# Register your models here.
admin.site.register(SubmissionAnalytics)
admin.site.register(QuestionAnalytics)
# admin.site.register(EventAnalytics)