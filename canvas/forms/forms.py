from django import forms
from django.forms import widgets
from canvas.models import Event, EVENT_TYPE_CHOICES
from datetime import datetime


class CreateEventForm(forms.ModelForm):
    name = forms.CharField(
        label="Event Name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    count_for_tokens = forms.BooleanField(
        label="Does this event count for tokens?",
        widget=forms.CheckboxInput(attrs={'style': 'transform: scale(1.5); margin: 5px'}),
        required=False
    )

    start_date = forms.DateTimeField(
        label="Start Date",
        widget=forms.DateTimeInput(attrs={'class': 'form-control datetimepicker'}),
        initial=datetime.now()
    )

    end_date = forms.DateTimeField(
        label="End Date",
        widget=forms.DateTimeInput(attrs={'class': 'form-control datetimepicker'}),
        initial=datetime.now()
    )

    type = forms.ChoiceField(
        label="Event Type",
        required=False,
        choices=EVENT_TYPE_CHOICES,
        widget=widgets.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Event
        fields = ['name', 'count_for_tokens', 'start_date', 'end_date', 'type']
