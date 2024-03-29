# Generated by Django 3.0.14 on 2021-04-21 05:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("course", "0011_auto_20201213_1913"),
    ]

    operations = [
        migrations.AlterField(
            model_name="questioncategory",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sub_categories",
                to="course.QuestionCategory",
            ),
        ),
    ]
