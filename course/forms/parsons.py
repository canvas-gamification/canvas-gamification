from django import forms

from course.fields import JSONLineFormField
from course.forms.forms import JunitProblemCreateForm
from course.models.parsons_question import ParsonsQuestion


class ParsonsQuestionForm(JunitProblemCreateForm):
    class Meta:
        model = ParsonsQuestion
        fields = (
            'title', 'difficulty', 'category', 'text', 'lines', 'junit_template', 'additional_file_name', 'variables',
            'event')
        exclude = ('answer',)

    answer = None

    lines = JSONLineFormField(
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        help_text="""
            Paste the solution here. Possibly add extra lines at the end.
            Lines will be extracted and shuffled.
            """
    )
