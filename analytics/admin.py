from django.contrib import admin

from analytics.models import JavaSubmissionAnalytics, ParsonsSubmissionAnalytics, MCQSubmissionAnalytics
from analytics.models.models import SubmissionAnalytics

admin.site.register(SubmissionAnalytics)
admin.site.register(QuestionAnalytics)
admin.site.register(JavaSubmissionAnalytics)
admin.site.register(ParsonsSubmissionAnalytics)
admin.site.register(MCQSubmissionAnalytics)
