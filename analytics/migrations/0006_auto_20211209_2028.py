# Generated by Django 3.0.14 on 2021-12-10 04:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('analytics', '0005_javaquestionanalytics_mcqquestionanalytics_parsonsquestionanalytics_questionanalytics'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='javaquestionanalytics',
            options={'base_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='javasubmissionanalytics',
            options={'base_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='mcqquestionanalytics',
            options={'base_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='mcqsubmissionanalytics',
            options={'base_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='parsonsquestionanalytics',
            options={'base_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='parsonssubmissionanalytics',
            options={'base_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='questionanalytics',
            options={'base_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='submissionanalytics',
            options={'base_manager_name': 'objects'},
        ),
        migrations.AddField(
            model_name='questionanalytics',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='polymorphic_analytics.questionanalytics_set+',
                                    to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='submissionanalytics',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='polymorphic_analytics.submissionanalytics_set+',
                                    to='contenttypes.ContentType'),
        ),
        
    ]