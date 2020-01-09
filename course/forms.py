from django import forms
from djrichtextfield.widgets import RichTextWidget

from course.models import Problem


class ProblemCreateForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ('title', 'text')

    text = forms.CharField(widget=RichTextWidget(field_settings='advanced'))
