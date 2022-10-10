# Generated by Django 3.0.14 on 2022-09-20 02:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_auto_20210811_1303'),
    ]

    operations = [
        migrations.AddField(
            model_name='userconsent',
            name='gender',
            field=models.CharField(blank=True, choices=[('MALE', 'Male'), ('FEMALE', 'Female'), ('NB', 'Non-binary'), ('OTHER', 'Other'), ('N/A', 'Prefer not to answer')], max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='userconsent',
            name='race',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]