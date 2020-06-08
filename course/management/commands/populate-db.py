from django.core.management import BaseCommand

from course.models import QuestionCategory, MultipleChoiceQuestion
from course.utils import create_multiple_choice_question


class Command(BaseCommand):
    help = 'Populate Database with sample problems'

    def add_arguments(self, parser):
        parser.add_argument('--category', action='store_true', help='Populate categories')
        parser.add_argument('--multiple-choice', action='store_true', help='Create sample multiple choice questions')
        parser.add_argument('--all', action='store_true', help='Populate db with all')

    def handle(self, *args, **options):
        if options['all']:
            self.populate_categories()
            self.populate_multiple_choice_questions()
            return
        if options['category']:
            self.populate_categories()
        if options['multiple_choice']:
            self.populate_multiple_choice_questions()

    def create_category_cluster(self, group_name, sub_categories):
        parent = QuestionCategory(name=group_name, description=group_name)
        parent.save()

        for category in sub_categories:
            QuestionCategory(name=category, description=category, parent=parent).save()

    def populate_categories(self):
        QuestionCategory.objects.all().delete()
        self.create_category_cluster('Basics', [
            "Variables",
            "Statements",
            "Constants",
            "Data Types",
            "Casting",
            "Arithmetic Operators",
            "Simple Calculation Programs"
        ])

    def populate_multiple_choice_questions(self):
        MultipleChoiceQuestion.objects.all().delete()
        create_multiple_choice_question(
            title='Question 1',
            text='What is the purpose of a variable in Java?',
            answer='a',
            max_submission_allowed=4,
            tutorial=None,
            author=None,
            category=QuestionCategory.objects.first() if QuestionCategory.objects.all().exists() else None,
            difficulty="EASY",
            is_verified=True,
            variables=[{}],
            choices={
                'a': 'Used to store data that can be used or modified as needed',
                'b': 'Used to repeatedly perform a single task',
                'c': 'Used to identify a portion of the program',
                'd': 'Used to change the appearance of the program',
            },
            visible_distractor_count=3,
            answer_text=None,
            distractors=None,
        )
        create_multiple_choice_question(
            title='Question 2',
            text='According to Java naming conventions, which of the following is a variable:',
            answer='a',
            max_submission_allowed=4,
            tutorial=None,
            author=None,
            category=QuestionCategory.objects.first() if QuestionCategory.objects.all().exists() else None,
            difficulty="EASY",
            is_verified=True,
            variables=[{}],
            choices={
                'a': 'distanceCovered',
                'b': 'DISTANCE_COVERED',
                'c': 'Distance Covered',
                'd': 'distance Covered',
            },
            visible_distractor_count=3,
            answer_text=None,
            distractors=None,
        )