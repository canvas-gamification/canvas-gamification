from django.contrib.auth.models import AbstractUser


# Create your models here.

class MyUser(AbstractUser):
    @property
    def new_messages_count(self):
        return self.received_messages.filter(read=False).count()

    @property
    def has_name(self):
        return self.first_name is not None and self.first_name != ""

    @property
    def has_complete_profile(self):
        return self.has_name
