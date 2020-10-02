from django import forms
from django.forms import TextInput, widgets, Textarea
from django.template.loader import render_to_string
from djrichtextfield.widgets import RichTextWidget
from rest_framework.reverse import reverse_lazy

from canvas.models import Event, CanvasCourse

from course.fields import JSONFormField
from course.models.models import DIFFICULTY_CHOICES, QuestionCategory
from course.widgets import JSONEditor, DynamicSelect


class ProblemCreateForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['difficulty'].widget.attrs.update({'class': 'form-control'})
        self.fields['difficulty'].initial = "EASY"
        self.fields['course'].queryset = CanvasCourse.objects.filter(instructor=user).all()

        if 'course' in self.data:
            course_id = int(self.data.get('course', -1))
        elif 'instance' in kwargs and kwargs.get('instance').course:
            course_id = kwargs.get('instance').course.pk
        else:
            course_id = None

        if course_id:
            self.fields['event'].queryset = Event.objects.filter(course_id=course_id).all()

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

    category = forms.ModelChoiceField(
        required=True,
        queryset=QuestionCategory.objects.filter(parent__isnull=False).all(),
        widget=widgets.Select(attrs={
            'class': 'form-control',
        })
    )

    course = forms.ModelChoiceField(
        label="Course",
        required=False,
        queryset=CanvasCourse.objects.none(),
        widget=widgets.Select(attrs={
            'class': 'form-control',
        })
    )

    event = forms.ModelChoiceField(
        label="Type",
        required=False,
        queryset=Event.objects.none(),
        widget=DynamicSelect(attrs={
            'class': 'form-control',
            'options_url': reverse_lazy('canvas:course_events_options'),
            'options_parameter_name': 'course_id',
            'options_parent_id': 'id_course',  # TODO: find a way not to hard code this
        })
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
        help_text="""
        If you are not using variables,
        please don't add any variables
        and delete the existing ones.
        """
    )


class JunitProblemCreateForm(ProblemCreateForm):
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

    additional_file_name = forms.CharField(
        label="User Code File Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }),
        required=False,
        help_text="""
            Provide a file name to put the user code in it when compiling.
            Leave empty if the user code is not a complete java program.
            This has no interference with {{code}} tag in the Junit template, you can use both.
            By providing a name here a file with that name will be created in the same directory
            of your Junit code and will be compiled with you Junit code.

            This name usually should be the exact name of the Java class with .java extension.
            For example if the solution has a public class Calculator, the file name should be
            Calculator.java
            """
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
