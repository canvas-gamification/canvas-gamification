from django import forms
from djrichtextfield.widgets import RichTextWidget

from course.fields import JSONFormField
from course.forms.forms import ProblemCreateForm
from course.models.multiple_choice import MultipleChoiceQuestion
from course.widgets import RadioInlineSelect


class ChoiceProblemCreateForm(ProblemCreateForm):
    choices = JSONFormField(
        widget=forms.HiddenInput(),
        initial='{}',
    )


class MultipleChoiceQuestionForm(ChoiceProblemCreateForm):
    class Meta:
        model = MultipleChoiceQuestion
        fields = (
            'title', 'difficulty', 'category', 'course', 'event', 'text', 'visible_distractor_count', 'variables')

    visible_distractor_count = forms.ChoiceField(
        choices=[('999', 'All'), ('2', '2'), ('3', '3')],
        initial='All',
        widget=RadioInlineSelect()
    )

    choices = None
    answer = None


class ChoiceForm(forms.Form):
    text = forms.CharField(
        label='Answer',
        widget=RichTextWidget(field_settings='basic')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_permitted = False
