from django import forms
from django.forms import Form, TextInput, CheckboxInput, DateTimeInput, DateInput, TimeInput, SplitDateTimeWidget, Select
from canvas.models import CanvasCourse
import datetime

# CHOICES =

class CreateEventForm(forms.Form):
    name = forms.CharField(
        label="Event Name",
        max_length=500,
        widget = TextInput(attrs={'class': 'form-control'})
    )
    # course = forms.ForeignKey(CanvasCourse, related_name='events', on_delete=models.CASCADE)
    course = forms.ModelChoiceField(
        label="Course",
        queryset=CanvasCourse.objects.all(),
        widget = Select(
            attrs={'class': 'form-control'}
        ),
    )
    count_for_tokens = forms.BooleanField(
        label="Does this event count for tokens?",
        widget = CheckboxInput(attrs={'class': 'form-control'})
    )

    start_datetime = forms.DateTimeField(
        label="Start Date/Time",
        widget = SplitDateTimeWidget(attrs={'class': 'form-control date'}),
        initial = datetime.datetime.now()
    )

    end_datetime = forms.DateTimeField(
        label="End Date/Time",
        widget = SplitDateTimeWidget(attrs={'class': 'form-control date'}),
        initial = datetime.datetime.now()
    )