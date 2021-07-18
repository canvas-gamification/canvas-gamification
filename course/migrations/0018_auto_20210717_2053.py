from django.db import migrations


def fix_java_input_files(apps, schema_editor):
    JavaQuestion = apps.get_model('course', 'JavaQuestion')
    for question in JavaQuestion.objects.all():
        input_files = []
        for input_file in question.input_file_names:
            try:
                input_files.append({
                    'name': input_file['name'],
                    'compile': True,
                    'template': input_file['template'],
                })
            except:
                pass
        question.input_files = input_files
        question.save()


class Migration(migrations.Migration):
    dependencies = [
        ('course', '0017_javaquestion_input_files'),
    ]

    operations = [
        migrations.RunPython(fix_java_input_files, migrations.RunPython.noop)
    ]
