# Generated by Django 3.0.14 on 2021-10-15 23:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0008_auto_20211015_1605'),
        ('course', '0020_question_question_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='userquestionjunction',
            name='report',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='general.QuestionReport'),
        ),
    ]