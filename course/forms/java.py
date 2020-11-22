from django.template.loader import render_to_string

from course.fields import JSONFormField
from course.forms.forms import JunitProblemCreateForm
from course.models.models import JavaQuestion
from course.widgets import JSONEditor


class JavaQuestionForm(JunitProblemCreateForm):
    class Meta:
        model = JavaQuestion
        fields = (
            'title', 'difficulty', 'category', 'course', 'event', 'text', 'junit_template', 'input_file_names',
            'variables')
        exclude = ('answer',)

    answer = None
    additional_file_name = None

    input_file_names = JSONFormField(
        initial='[]',
        label='',
        widget=JSONEditor(schema=render_to_string('schemas/input_file_names.json')),
        help_text="""
            Please provide the name of the
            files students need to submit.
            Each file will be compiled with the junit.
            """
    )
