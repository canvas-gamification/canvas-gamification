from django.db import migrations, models
from accounts.utils.generate_default_name import generate_default_name


def forwards_func(apps, schema_editor):
    MyUser = apps.get_model("accounts", "myuser")
    my_users = MyUser.objects.select_for_update()
    for my_user in my_users:
        my_user.nickname = generate_default_name()
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
            model_name='myuser',
            name='nickname',
            field=models.CharField(max_length=100, verbose_name="nickname"),
            preserve_default=False,
        ),
    ]
