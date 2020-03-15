from django import forms
from django.contrib import admin

# Register your models here.
from djrichtextfield.widgets import RichTextWidget

from course.models import Question, VariableQuestion, MultipleChoiceQuestion, Submission, QuestionCategory, \
    CheckboxQuestion, JavaSubmission


class QuestionAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(QuestionAdminForm, self).__init__(*args, **kwargs)

        self.fields['text'].widget = RichTextWidget(field_settings='advanced')
        self.fields['tutorial'].widget = RichTextWidget(field_settings='advanced')

    class Meta:
        model = Question
        exclude = []


class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm


class MultipleChoiceQuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm


class CheckboxQuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm


admin.site.register(Question, QuestionAdmin)
admin.site.register(VariableQuestion)
admin.site.register(MultipleChoiceQuestion, MultipleChoiceQuestionAdmin)
admin.site.register(CheckboxQuestion, CheckboxQuestionAdmin)
admin.site.register(Submission)
admin.site.register(QuestionCategory)
admin.site.register(JavaSubmission)
