# Generated by Django 3.0.14 on 2023-01-06 02:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("general", "0012_auto_20221231_1039"),
    ]

    operations = [
        migrations.CreateModel(
            name="Survey",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("time_created", models.DateTimeField(auto_now_add=True)),
                ("time_modified", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=100)),
                ("response", jsonfield.fields.JSONField(null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="surveys", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
        ),
    ]
