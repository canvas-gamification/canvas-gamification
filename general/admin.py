# Register your models here.
from django.contrib import admin

from general.models.action import Action
from general.models.contact_us import ContactUs
from general.models.faq import FAQ
from general.models.question_report import QuestionReport


class FAQAdmin(admin.ModelAdmin):
    list_display = ("__str__", "question")


class ActionAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "description",
        "actor",
        "token_change",
        "status",
    )
    list_filter = ("status",)


class QuestionReportAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "report")
    list_filter = (
        "user",
        "question",
    )


admin.site.register(FAQ, FAQAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(ContactUs)
admin.site.register(QuestionReport, QuestionReportAdmin)
