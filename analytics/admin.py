from django.contrib import admin
from analytics.models import JavaSubmissionAnalytics, ParsonsSubmissionAnalytics, MCQSubmissionAnalytics
from analytics.models.java import JavaQuestionAnalytics
from analytics.models.mcq import MCQQuestionAnalytics
from analytics.models.models import SubmissionAnalytics, QuestionAnalytics
from analytics.models.parsons import ParsonsQuestionAnalytics

admin.site.register(SubmissionAnalytics)
admin.site.register(JavaSubmissionAnalytics)
admin.site.register(ParsonsSubmissionAnalytics)
admin.site.register(MCQSubmissionAnalytics)
admin.site.register(QuestionAnalytics)
admin.site.register(JavaQuestionAnalytics)
admin.site.register(ParsonsQuestionAnalytics)
admin.site.register(MCQQuestionAnalytics)