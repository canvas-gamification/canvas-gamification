# Generated by Django 3.0.14 on 2021-12-07 05:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0020_question_question_status'),
        ('canvas', '0009_auto_20210702_1305'),
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionanalytics',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='canvas.Event'),
        ),
        migrations.AlterField(
            model_name='questionanalytics',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='course.Question'),
        ),
    ]