# Generated by Django 3.0.14 on 2022-07-03 01:47

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('canvas', '0011_merge_20211116_1744'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='max_team_size',
            field=models.IntegerField(default=3, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('time_modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('is_private', models.BooleanField(default=False)),
                ('course_registrations', models.ManyToManyField(to='canvas.CanvasCourseRegistration')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='canvas.Event')),
                ('who_can_join', models.ManyToManyField(to='canvas.CanvasCourseRegistration')),
            ],
        ),
    ]