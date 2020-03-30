from django.contrib import admin

# Register your models here.
from django import forms
from djrichtextfield.widgets import RichTextWidget

from general.models import FAQ, Action


class FAQAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(FAQAdminForm, self).__init__(*args, **kwargs)

        self.fields['answer'].widget = RichTextWidget(field_settings='advanced')

    class Meta:
        model = FAQ
        exclude = []


class FAQAdmin(admin.ModelAdmin):
    form = FAQAdminForm


admin.site.register(FAQ, FAQAdmin)
admin.site.register(Action)