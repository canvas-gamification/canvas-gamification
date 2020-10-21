from django import forms
from django.forms import TextInput, CheckboxInput, DateTimeInput, Select
from canvas.models import CanvasCourse
from datetime import datetime


class CreateEventForm(forms.Form):
    name = forms.CharField(
        label="Event Name",
        max_length=500,
        widget=TextInput(attrs={'class': 'form-control'})
    )

    course = forms.ModelChoiceField(
        label="Course",
        queryset=CanvasCourse.objects.all(),
        widget=Select(
            attrs={'class': 'form-control'}
        ),
    )
    count_for_tokens = forms.BooleanField(
        label="Does this event count for tokens?",
        widget=CheckboxInput(attrs={'class': 'form-control'}),
        required=False
    )

    start_datetime = forms.DateTimeField(
        label="Start Date/Time (YYYY-MM-DD HH:MM:SS)",
        widget=DateTimeInput(attrs={'class': 'form-control date'}),
        initial=datetime.now()
    )

    end_datetime = forms.DateTimeField(
        label="End Date/Time (YYYY-MM-DD HH:MM:SS)",
        widget=DateTimeInput(attrs={'class': 'form-control date'}),
        initial=datetime.now()
    )
