# Generated by Django 3.0.7 on 2020-09-22 03:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("course", "0005_question_event"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="javaquestion",
            name="test_cases",
        ),
        migrations.AddField(
            model_name="javaquestion",
            name="additional_file_name",
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="javaquestion",
            name="junit_template",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
    ]
