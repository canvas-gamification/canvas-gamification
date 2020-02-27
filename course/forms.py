from django import forms
from djrichtextfield.widgets import RichTextWidget

from course.models import MultipleChoiceQuestion


class ProblemCreateForm(forms.ModelForm):
    class Meta:
        model = MultipleChoiceQuestion
        fields = ('title', 'text', 'answer', 'tutorial', 'category', 'variables', 'choices')

    text = forms.CharField(label='Statement', widget=RichTextWidget(field_settings='advanced'))
    tutorial = forms.CharField(label='Statement', widget=RichTextWidget(field_settings='advanced'))

