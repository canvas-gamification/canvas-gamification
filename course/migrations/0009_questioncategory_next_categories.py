# Generated by Django 3.0.7 on 2020-11-22 00:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0008_question_is_sample'),
    ]

    operations = [
        migrations.AddField(
            model_name='questioncategory',
            name='next_categories',
            field=models.ManyToManyField(blank=True, related_name='prev_categories', to='course.QuestionCategory'),
        ),
    ]