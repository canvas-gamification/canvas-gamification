# Generated by Django 3.0.7 on 2020-10-13 06:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("canvas", "0006_canvascourse_instructor"),
    ]

    operations = [
        migrations.AddField(
            model_name="tokenuse",
            name="num_used",
            field=models.IntegerField(default=0),
        ),
    ]
