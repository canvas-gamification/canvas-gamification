import json

from django.shortcuts import get_object_or_404
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

    def populate_categories(self):
        for q in QuestionCategory.objects.all():
            q.question_set.all().delete()
            q.delete()

        with open('import/categories.json') as f:
            category_links = json.loads(f.read())

            def get_top_categories(category_tuple):
                if category_tuple[1]['parent'] is None:
                    return True
                else:
                    return False

            top_categories = filter(get_top_categories, category_links.items())

            for parent_id, parent_data in top_categories:
                print("parent", parent_id)
                parent_name = parent_data['name']
                parent = QuestionCategory(pk=parent_id, name=parent_name, description=parent_name)
                parent.save()

                def get_child_categories(category_tuple):
                    return category_tuple[1]['parent'] == int(parent_id)

                child_categories = filter(get_child_categories, category_links.items())

                for child_id, child_data in child_categories:
                    child_name = child_data['name']
                    child = QuestionCategory(pk=child_id, name=child_name, description=child_name, parent=parent)
                    print("--", child_id)
                    child.save()

            for category_id, category_data in category_links.items():
                print("Next:", category_id)
                category = get_object_or_404(QuestionCategory, pk=int(category_id))
                next_categories = category_data['linkedTo']
                if next_categories is not None:
                    for next_category_id in next_categories:
                        print("--", next_category_id)
                        next_category = get_object_or_404(QuestionCategory, pk=next_category_id)
                        category.next_categories.add(next_category)
                    category.save()

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
