from django.contrib import admin

# Register your models here.
from course.models import Question, VariableQuestion, MultipleChoiceQuestion, Submission, QuestionCategory

admin.site.register(Question)
admin.site.register(VariableQuestion)
admin.site.register(MultipleChoiceQuestion)
admin.site.register(Submission)
admin.site.register(QuestionCategory)
