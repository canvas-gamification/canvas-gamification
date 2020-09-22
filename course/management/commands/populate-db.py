import json

from django.core.management import BaseCommand

from course.models.models import QuestionCategory, MultipleChoiceQuestion, JavaQuestion
from course.utils.utils import create_multiple_choice_question, create_java_question


class Command(BaseCommand):
    help = 'Populate Database with sample problems'

    def add_arguments(self, parser):
        parser.add_argument('--category', action='store_true', help='Populate categories')
        parser.add_argument('--java', action='store_true', help='Create sample java questions')
        parser.add_argument('--multiple-choice', action='store_true', help='Create sample multiple choice questions')
        parser.add_argument('--all', action='store_true', help='Populate db with all')

    def handle(self, *args, **options):
        if options['all']:
            self.populate_categories()
            self.populate_multiple_choice_questions()
            self.populate_java_questions()
            return
        if options['category']:
            self.populate_categories()
        if options['multiple_choice']:
            self.populate_multiple_choice_questions()
        if options['java']:
            self.populate_java_questions()

    def create_category_cluster(self, group_name, sub_categories):
        parent = QuestionCategory(name=group_name, description=group_name)
        parent.save()

        for category in sub_categories:
            QuestionCategory(name=category, description=category, parent=parent).save()

    def populate_categories(self):
        QuestionCategory.objects.all().delete()

        with open('import/categories.json') as f:
            categories = json.loads(f.read())
            for group_name, sub_categories in categories.items():
                self.create_category_cluster(group_name, sub_categories)

    def populate_multiple_choice_questions(self):
        MultipleChoiceQuestion.objects.all().delete()

        with open('import/multiple_choice_questions.json') as f:
            questions = json.loads(f.read())
            for question in questions:
                create_multiple_choice_question(
                    title=question['title'],
                    text=question['text'],
                    answer='a',
                    max_submission_allowed=4,
                    tutorial=None,
                    author=None,
                    category=QuestionCategory.objects.first() if QuestionCategory.objects.all().exists() else None,
                    difficulty="EASY",
                    is_verified=True,
                    variables=[],
                    choices=question['choices'],
                    visible_distractor_count=3,
                    answer_text=None,
                    distractors=None,
                )

    def populate_java_questions(self):
        JavaQuestion.objects.all().delete()
        with open('import/java_questions.json') as f:
            questions = json.loads(f.read())
            for question in questions:
                create_java_question(
                    title=question['title'],
                    text=question['text'],
                    max_submission_allowed=5,
                    tutorial=None,
                    author=None,
                    category=QuestionCategory.objects.first() if QuestionCategory.objects.all().exists() else None,
                    difficulty="EASY",
                    is_verified=True,
                    junit_template=question['junit_template'],
                    additional_file_name=question['additional_file_name']
                )
