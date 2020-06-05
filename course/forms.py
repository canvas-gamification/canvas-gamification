from django import forms
from django.forms import TextInput, Textarea, NumberInput, widgets, formset_factory
from djrichtextfield.widgets import RichTextWidget
from jsoneditor.forms import JSONEditor
from jsonfield.forms import JSONFormField

from course.models import MultipleChoiceQuestion, DIFFICULTY_CHOICES, CheckboxQuestion, JavaQuestion, QuestionCategory
from course.widgets import RadioInlineSelect


class ProblemCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['category'].widget.attrs.update({'class': 'form-control'})
        self.fields['difficulty'].widget.attrs.update({'class': 'form-control'})
        self.fields['difficulty'].initial = "EASY"

    title = forms.CharField(
        label="Question Name",
        widget=TextInput(attrs={
            'class': 'form-control'
        })
    )

    text = forms.CharField(
        label='Question',
        widget=RichTextWidget(field_settings='advanced')
    )

    answer = forms.CharField(
        initial="",
        widget=forms.HiddenInput(attrs={
            'class': 'form-control',
        })
    )


class ChoiceProblemCreateForm(ProblemCreateForm):
    variables = JSONFormField(
        initial='[{}]',
        widget=forms.HiddenInput(),
    )

    choices = JSONFormField(
        widget=forms.HiddenInput(),
        initial='{}',
    )


class ProblemFilterForm(forms.Form):
    query = forms.CharField(
        label='Search in Question Name',
        required=False,
        widget=widgets.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search in the problem set...',
        })
    )

    difficulty = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + DIFFICULTY_CHOICES,
        widget=widgets.Select(attrs={
            'class': 'form-control',
        })
    )

    category = forms.ModelChoiceField(
        required=False,
        empty_label='All',
        queryset=QuestionCategory.objects.filter(parent__isnull=True).all(),
        widget=widgets.Select(attrs={
            'class': 'form-control',
        })
    )

    solved = forms.ChoiceField(
        label='Status',
        required=False,
        choices=[('', 'All'), ('Solved', 'Solved'), ('Partially Correct', 'Partially Correct'),
                 ('Unsolved', 'Unsolved'), ('Wrong', 'Wrong'),
                 ('New', 'New')],
        widget=widgets.Select(attrs={
            'class': 'form-control',
        })
    )


class CheckboxQuestionForm(ChoiceProblemCreateForm):
    class Meta:
        model = CheckboxQuestion
        fields = (
            'title', 'difficulty', 'category', 'text', 'visible_distractor_count')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    visible_distractor_count = forms.ChoiceField(
        choices=[('999', 'All'), ('2', '2'), ('3', '3')],
        initial='All',
        widget=RadioInlineSelect()
    )

    answer = None
    variables = None
    choices = None


class MultipleChoiceQuestionForm(ChoiceProblemCreateForm):
    class Meta:
        model = MultipleChoiceQuestion
        fields = (
            'title', 'difficulty', 'category', 'text', 'visible_distractor_count')

    visible_distractor_count = forms.ChoiceField(
        choices=[('999', 'All'), ('2', '2'), ('3', '3')],
        initial='All',
        widget=RadioInlineSelect()
    )

    variables = None
    choices = None
    answer = None


class JavaQuestionForm(ProblemCreateForm):
    class Meta:
        model = JavaQuestion
        fields = (
            'title', 'difficulty', 'category', 'text', 'test_cases')
        exclude = ('answer',)

    answer = None

    test_cases = JSONFormField(
        widget=JSONEditor(),
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


class ChoiceForm(forms.Form):
    text = forms.CharField(
        label='Answer',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_permitted = False
