# Generated by Django 3.0.14 on 2022-10-24 18:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("canvas", "0015_auto_20221023_1301"),
    ]

    operations = [
        migrations.AddField(
            model_name="canvascourse",
            name="description",
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]