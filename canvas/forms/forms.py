from django import forms
from canvas.models import Event
from datetime import datetime


class CreateEventForm(forms.ModelForm):
    name = forms.CharField(
        label="Event Name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    count_for_tokens = forms.BooleanField(
        label="Does this event count for tokens?",
        widget=forms.CheckboxInput(attrs={'class': 'form-control'}),
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

    class Meta:
        model = Event
        # fields = ['name', 'course', 'count_for_tokens', 'start_date', 'end_date']
        fields = ['name', 'count_for_tokens', 'start_date', 'end_date']
