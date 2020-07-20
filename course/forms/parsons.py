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
            'title', 'difficulty', 'category', 'text', 'lines', 'junit_template',
            'additional_file_name', 'variables', )
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
