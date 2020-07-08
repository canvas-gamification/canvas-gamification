from django import forms
from django.forms import TextInput, widgets
from django.template.loader import render_to_string
from djrichtextfield.widgets import RichTextWidget
from course.fields import JSONFormField
from django.contrib.staticfiles.storage import staticfiles_storage
from course.models.models import DIFFICULTY_CHOICES, QuestionCategory
from course.widgets import JSONEditor


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

    variables = JSONFormField(
        initial='[]',
        label='',
        widget=JSONEditor(
            schema=render_to_string('schemas/variables.json'),
            doc_url='/docs/usage/variables.html',
        ),
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
