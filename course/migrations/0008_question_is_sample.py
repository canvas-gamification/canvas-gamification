# Generated by Django 3.0.7 on 2020-10-27 03:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("course", "0007_auto_20201002_0329"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="is_sample",
            field=models.BooleanField(default=False),
        ),
    ]
