from django.template.loader import render_to_string

from course.fields import JSONFormField
from course.forms.forms import ProblemCreateForm
from course.models.models import JavaQuestion
from course.widgets import JSONEditor


class JavaQuestionForm(ProblemCreateForm):
    class Meta:
        model = JavaQuestion
        fields = (
            'title', 'difficulty', 'category', 'text', 'test_cases')
        exclude = ('answer',)

    answer = None
    variables = None

    test_cases = JSONFormField(
        widget=JSONEditor(schema=render_to_string('schemas/test_cases.json')),
        help_text="""
        It should be an array if test_cases each element need to have input and outpur.
        A valid example:
        [
            {
                "input": "2",
                "output": "Even"
            },
            {
                "input": "3",
                "output": "Odd"
            }
        ]
        """
    )