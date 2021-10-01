from course.models.models import QuestionCategory
from course.utils.utils import create_multiple_choice_question, create_java_question


def add_base_category():
    category = QuestionCategory(name="category", description="category")
    category.save()
    return category


def add_base_questions(user, category, event):
    for i in range(10):
        create_multiple_choice_question(
            title="title",
            text='text',
            answer='a',
            max_submission_allowed=999,
            tutorial='tt',
            author=user,
            category=category,
            difficulty="EASY",
            is_verified=True,
            variables='[]',
            choices={'a': 'a', 'b': 'b'},
            visible_distractor_count=3,
            event=event
        )
        create_java_question(
            title='title',
            text='text',
            max_submission_allowed=999,
            tutorial='tutorial',
            author=user,
            category=category,
            difficulty='EASY',
            is_verified=True,
            junit_template='',
            input_files=[
                {
                    'name': 'A.java',
                    'compile': False,
                    'template': '',
                },
                {
                    'name': 'B.java',
                    'compile': True,
                    'template': '',
                },
                {
                    'name': 'C.java',
                    'compile': False,
                    'template': '',
                }
            ],
            event=event
        )
