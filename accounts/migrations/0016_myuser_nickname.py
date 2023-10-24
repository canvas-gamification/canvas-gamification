import random

from django.db import migrations, models
from accounts.utils.nicknames import get_all_nicknames


def forwards_func(apps, schema_editor):
    MyUser = apps.get_model("accounts", "myuser")
    my_users = MyUser.objects.select_for_update()
    all_available_nicknames = get_all_nicknames()
    random.shuffle(all_available_nicknames)
    all_available_nicknames = set(all_available_nicknames)

    for my_user in my_users:
        if len(all_available_nicknames) <= 0:
            raise ValueError("No more available nicknames")

        new_nickname = all_available_nicknames.pop()
        my_user.nickname = new_nickname
        my_user.save()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0015_auto_20220919_1956"),
    ]

    operations = [
        migrations.AddField(
            model_name="myuser",
            name="nickname",
            field=models.CharField(max_length=100, null=True, verbose_name="nickname"),
            preserve_default=False,
        ),
        migrations.RunPython(forwards_func),
        migrations.AlterField(
            model_name="myuser",
            name="nickname",
            field=models.CharField(max_length=100, verbose_name="nickname"),
            preserve_default=False,
        ),
    ]
