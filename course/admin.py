from django import forms
from django.contrib import admin
from djrichtextfield.widgets import RichTextWidget

from course.models.models import Question, VariableQuestion, Submission, QuestionCategory, \
    TokenValue, UserQuestionJunction
from course.models.java import JavaQuestion, JavaSubmission
from course.models.multiple_choice import MultipleChoiceQuestion, MultipleChoiceSubmission
from course.models.parsons import ParsonsQuestion, ParsonsSubmission


class QuestionAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(QuestionAdminForm, self).__init__(*args, **kwargs)

        self.fields['text'].widget = RichTextWidget(field_settings='advanced')
        self.fields['tutorial'].widget = RichTextWidget(field_settings='advanced')

    class Meta:
        model = Question
        exclude = []


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'title', 'author', 'category', 'difficulty', 'is_verified',)
    list_filter = ('author', 'category', 'difficulty', 'is_verified',)
    form = QuestionAdminForm


class SubmissionAdmin(admin.ModelAdmin):
    list_filter = ('uqj__user__username', 'is_correct', 'is_partially_correct', 'uqj__question')
    list_display = ('__str__', 'grade', 'is_correct', 'is_partially_correct')


class TokenValueAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'category', 'difficulty', 'value')


class UserQuestionJunctionAdmin(admin.ModelAdmin):
    list_filter = ('user__username', 'question')
    list_display = ('user', 'question', 'is_solved', 'is_partially_solved', 'is_favorite')


admin.site.register(Question, QuestionAdmin)
admin.site.register(VariableQuestion, QuestionAdmin)
admin.site.register(MultipleChoiceQuestion, QuestionAdmin)
admin.site.register(JavaQuestion, QuestionAdmin)
admin.site.register(ParsonsQuestion, QuestionAdmin)

admin.site.register(Submission, SubmissionAdmin)
admin.site.register(MultipleChoiceSubmission, SubmissionAdmin)
admin.site.register(JavaSubmission, SubmissionAdmin)
admin.site.register(ParsonsSubmission, SubmissionAdmin)

admin.site.register(TokenValue, TokenValueAdmin)
admin.site.register(UserQuestionJunction, UserQuestionJunctionAdmin)
admin.site.register(QuestionCategory)
