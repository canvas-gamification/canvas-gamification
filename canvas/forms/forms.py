from django import forms
from canvas.models import Event
from datetime import datetime
from canvas.models import CanvasCourse
from django.shortcuts import get_object_or_404


class CreateEventForm(forms.ModelForm):
    def __init__(self, course_pk: int, *args, **kwargs):
        super(CreateEventForm, self).__init__(*args, **kwargs)
        # self.fields['course'] = forms.ModelChoiceField(
        #     label="Course",
        #     queryset=CanvasCourse.objects.filter(pk=course_pk),
        #     widget=forms.Select(
        #         attrs={'class': 'form-control'}
        #     )
        # )

    # initial=get_object_or_404(CanvasCourse, pk=course_pk)

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
