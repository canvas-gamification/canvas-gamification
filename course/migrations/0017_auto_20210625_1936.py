# Generated by Django 3.0.14 on 2021-06-26 02:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0016_merge_20210625_1829'),
    ]

    operations = [
        migrations.AddField(
            model_name='testmodel',
            name='coldStreak',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='testmodel',
            name='hotStreak',
            field=models.BooleanField(default=False),
        ),
    ]