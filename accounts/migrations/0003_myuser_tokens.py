# Generated by Django 3.0.3 on 2020-02-27 06:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_myuser_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="myuser",
            name="tokens",
            field=models.FloatField(default=0),
        ),
    ]
