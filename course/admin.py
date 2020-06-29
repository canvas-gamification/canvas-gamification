from django import forms
from django.contrib import admin

# Register your models here.
from djrichtextfield.widgets import RichTextWidget

from course.models.models import Question, VariableQuestion, MultipleChoiceQuestion, Submission, QuestionCategory, \
    CheckboxQuestion, JavaSubmission, JavaQuestion, TokenValue, MultipleChoiceSubmission
from course.models.parsons_question import ParsonsQuestion, ParsonsSubmission


class QuestionAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(QuestionAdminForm, self).__init__(*args, **kwargs)

        self.fields['text'].widget = RichTextWidget(field_settings='advanced')
        self.fields['tutorial'].widget = RichTextWidget(field_settings='advanced')

    class Meta:
        model = Question
        exclude = []


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'title', 'author', 'category', 'difficulty', 'is_verified', )
    list_filter = ('author', 'category', 'difficulty', 'is_verified', )
    form = QuestionAdminForm


class SubmissionAdmin(admin.ModelAdmin):
    list_filter = ('user__username', 'is_correct', 'is_partially_correct', 'question')
    list_display = ('__str__', 'user', 'grade', 'is_correct', 'is_partially_correct')


class TokenValueAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'category', 'difficulty', 'value')


admin.site.register(Question, QuestionAdmin)
admin.site.register(VariableQuestion, QuestionAdmin)
admin.site.register(MultipleChoiceQuestion, QuestionAdmin)
admin.site.register(CheckboxQuestion, QuestionAdmin)
admin.site.register(JavaQuestion, QuestionAdmin)
admin.site.register(ParsonsQuestion, QuestionAdmin)

admin.site.register(Submission, SubmissionAdmin)
admin.site.register(MultipleChoiceSubmission, SubmissionAdmin)
admin.site.register(JavaSubmission, SubmissionAdmin)
admin.site.register(ParsonsSubmission, SubmissionAdmin)

admin.site.register(TokenValue, TokenValueAdmin)
admin.site.register(QuestionCategory)
