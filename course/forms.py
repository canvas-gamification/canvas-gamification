from django import forms
from djrichtextfield.widgets import RichTextWidget

from course.models import Question


class ProblemCreateForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('title', 'text')

    text = forms.CharField(widget=RichTextWidget(field_settings='advanced'))
