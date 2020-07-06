from django import forms
from django.forms import Textarea
from django.template.loader import render_to_string

from course.widgets import JSONEditor
from course.fields import JSONFormField, JSONLineFormField

from course.forms.forms import ProblemCreateForm
from course.models.parsons_question import ParsonsQuestion


class ParsonsQuestionForm(ProblemCreateForm):
    class Meta:
        model = ParsonsQuestion
        fields = (
            'title', 'difficulty', 'category', 'text', 'lines', 'junit_template', 'variables')
        exclude = ('answer',)

    answer = None

    lines = JSONLineFormField(
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        help_text="""
            Paste the solution here. Possibly add extra lines at the end.
            Lines will be extracted and shuffled.
            """
    )

    junit_template = forms.CharField(
        label="JUnit Template",
        widget=Textarea(attrs={
            'class': 'form-control'
        }),
        help_text="""
            Please provide a JUnit template to evaluate the code.
            Identify where to insert the solution by "{{code}}"
            """
    )
