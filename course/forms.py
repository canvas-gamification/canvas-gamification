from django import forms
from django.forms import TextInput, Textarea, NumberInput, widgets
from djrichtextfield.widgets import RichTextWidget
from jsoneditor.forms import JSONEditor

from course.models import MultipleChoiceQuestion, DIFFICULTY_CHOICES


class ProblemCreateForm(forms.ModelForm):
    class Meta:
        model = MultipleChoiceQuestion
        fields = (
            'title', 'token_value', 'difficulty', 'text', 'answer', 'tutorial', 'category', 'variables', 'choices')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['category'].widget.attrs.update({'class': 'form-control'})
        self.fields['difficulty'].widget.attrs.update({'class': 'form-control'})

    title = forms.CharField(
        widget=TextInput(attrs={
            'class': 'form-control'
        })
    )

    token_value = forms.IntegerField(
        widget=NumberInput(attrs={
            'class': 'form-control'
        })
    )

    text = forms.CharField(
        label='Statement',
        widget=RichTextWidget(field_settings='advanced')
    )

    answer = forms.CharField(
        widget=Textarea(attrs={
            'class': 'form-control'
        })
    )

    tutorial = forms.CharField(
        widget=RichTextWidget(field_settings='advanced')
    )

    variables = forms.CharField(
        widget=JSONEditor(),
        help_text="""
        It should be an array with each element a set of variables to choose.
        A valid example:
        [
            {
                "x" : 1,
                "y" : 2,
            },
            {
                "x" : 5,
                "y" : 8,
            }
        ]
        """
    )

    choices = forms.CharField(
        widget=JSONEditor(),
        help_text="""
            It should be an object of choices.
            A valid example:
            {
                "a" : "{x} is odd and {y} is odd",
                "b" : "{x} is even and {y} is odd",
                "c" : "{x} is odd and {y} is even",
                "d" : "{x} is even and {y} is even"
            }
            """
    )


class ProblemFilterForm(forms.Form):
    query = forms.CharField(
        label='Search',
        required=False,
        widget=widgets.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search in the problem set...',
        })
    )

    difficulty = forms.ChoiceField(
        required=False,
        choices=[ ('All', 'All') ]+DIFFICULTY_CHOICES,
        widget=widgets.Select(attrs={
            'class': 'form-control',
        })
    )

    solved = forms.ChoiceField(
        required=False,
        choices=[('All', 'All'), ('Solved', 'Solved'), ('Unsolved', 'Unsolved'), ('Wrong', 'Wrong'),
                 ('Unopened', 'Unopened')],
        widget=widgets.Select(attrs={
            'class': 'form-control',
        })
    )
