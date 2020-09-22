from course.forms.forms import JunitProblemCreateForm
from course.models.models import JavaQuestion


class JavaQuestionForm(JunitProblemCreateForm):
    class Meta:
        model = JavaQuestion
        fields = (
            'title', 'difficulty', 'category', 'text', 'junit_template', 'additional_file_name', 'variables',)
        exclude = ('answer',)

    answer = None
