# Generated by Django 3.0.14 on 2021-10-15 20:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0008_auto_20211011_1604'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questionreport',
            name='report_timestamp',
        ),
    ]