from django.db import models

from accounts.utils.email_functions import send_contact_us_email


class ContactUs(models.Model):
    class Meta:
        verbose_name_plural = 'Contact Us'

    fullname = models.CharField(max_length=100)
    email = models.EmailField()
    comment = models.TextField()

    def save(self, **kwargs):
        super().save(**kwargs)
        send_contact_us_email(self.fullname, self.email, self.comment)
