"""Baseline tests for course/management/commands/populate-db.py.

The command reads the JSON fixtures in ``import/`` with paths relative to the
process cwd, so every test chdirs to ``settings.BASE_DIR`` first.

Cost note: the shipped fixtures are deliberately small (63 categories, 4 multiple
choice + 1 java + 1 parsons question), and these tests create **no** MyUser rows,
so ``Question.save()`` -> ``ensure_uqj()`` has no users to fan out over and the
whole ``--all`` run stays fast.  The one test that needs a pre-existing question
creates exactly one user and one question for the same reason.
"""

import json
import os

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from course.models.java import JavaQuestion
from course.models.models import Question, QuestionCategory, UserQuestionJunction
from course.models.multiple_choice import MultipleChoiceQuestion
from course.models.parsons import ParsonsQuestion
from test.baseline.fixtures_grader import create_category, create_java_question, create_user


def fixture(name):
    with open(os.path.join(str(settings.BASE_DIR), "import", name)) as f:
        return json.loads(f.read())


class PopulateDbChdirMixin(object):
    def setUp(self):
        super(PopulateDbChdirMixin, self).setUp()
        old_cwd = os.getcwd()
        os.chdir(str(settings.BASE_DIR))
        self.addCleanup(os.chdir, old_cwd)


class PopulateDbAllTests(PopulateDbChdirMixin, TestCase):
    """``populate-db --all`` end to end against the real import/*.json fixtures."""

    def test_all_creates_categories_and_questions(self):
        call_command("populate-db", "--all")

        categories = fixture("categories.json")
        self.assertEqual(QuestionCategory.objects.count(), len(categories))
        self.assertEqual(MultipleChoiceQuestion.objects.count(), len(fixture("multiple_choice_questions.json")))
        self.assertEqual(JavaQuestion.objects.count(), len(fixture("java_questions.json")))
        self.assertEqual(ParsonsQuestion.objects.count(), len(fixture("parsons_questions.json")))

        expected_total = (
            len(fixture("multiple_choice_questions.json"))
            + len(fixture("java_questions.json"))
            + len(fixture("parsons_questions.json"))
        )
        self.assertEqual(Question.objects.count(), expected_total)

    def test_all_wires_up_category_parents_and_links(self):
        call_command("populate-db", "--all")

        categories = fixture("categories.json")
        expected_roots = sum(1 for c in categories.values() if c["parent"] is None)
        self.assertEqual(QuestionCategory.objects.filter(parent__isnull=True).count(), expected_roots)

        expected_links = sum(len(c["linkedTo"]) for c in categories.values())
        total_links = sum(c.next_categories.count() for c in QuestionCategory.objects.all())
        self.assertEqual(total_links, expected_links)

        # names come straight from the fixture, and description mirrors name
        for category in QuestionCategory.objects.all():
            self.assertEqual(category.name, category.description)
        self.assertEqual(
            sorted(QuestionCategory.objects.values_list("name", flat=True)),
            sorted(c["name"] for c in categories.values()),
        )

    def test_created_questions_are_verified_easy_and_authorless(self):
        call_command("populate-db", "--all")

        self.assertFalse(Question.objects.filter(is_verified=False).exists())
        self.assertFalse(Question.objects.exclude(difficulty="EASY").exists())
        self.assertFalse(Question.objects.filter(author__isnull=False).exists())
        # every question is attached to QuestionCategory.objects.first()
        self.assertEqual(Question.objects.filter(category__isnull=True).count(), 0)

        mcq = MultipleChoiceQuestion.objects.first()
        self.assertEqual(mcq.answer, "a")
        self.assertEqual(mcq.max_submission_allowed, 4)
        self.assertEqual(mcq.visible_distractor_count, 3)
        self.assertEqual(JavaQuestion.objects.first().max_submission_allowed, 5)
        self.assertEqual(ParsonsQuestion.objects.first().max_submission_allowed, 5)

    def test_running_all_twice_is_idempotent(self):
        call_command("populate-db", "--all")
        first_counts = (
            QuestionCategory.objects.count(),
            Question.objects.count(),
        )
        call_command("populate-db", "--all")
        self.assertEqual((QuestionCategory.objects.count(), Question.objects.count()), first_counts)

    def test_all_detaches_and_deletes_pre_existing_data(self):
        """populate_categories nulls Question.category then wipes all categories."""
        user = create_user("populate_user")
        category = create_category("Pre-existing")
        question = create_java_question(author=user, category=category)
        self.assertEqual(UserQuestionJunction.objects.filter(user=user).count(), 1)

        call_command("populate-db", "--all")

        # the pre-existing JavaQuestion is deleted by populate_java_questions
        self.assertFalse(JavaQuestion.objects.filter(pk=question.pk).exists())
        self.assertFalse(QuestionCategory.objects.filter(name="Pre-existing").exists())
        # the new questions each got a UQJ for the one existing user
        self.assertEqual(UserQuestionJunction.objects.filter(user=user).count(), Question.objects.count())


class PopulateDbPartialFlagTests(PopulateDbChdirMixin, TestCase):
    """Anything other than --all currently blows up before it finishes."""

    def test_category_flag_alone_raises_key_error_parsons(self):
        # KNOWN-BUG: course/management/commands/populate-db.py:42 reads
        # options["parsons"], but add_arguments() (:19-27) never declares a
        # --parsons argument.  Every non---all invocation therefore ends in
        # KeyError: 'parsons' *after* doing its work.
        with self.assertRaises(KeyError) as ctx:
            call_command("populate-db", "--category")
        self.assertEqual(ctx.exception.args[0], "parsons")

    def test_category_flag_still_populated_categories_before_raising(self):
        with self.assertRaises(KeyError):
            call_command("populate-db", "--category")
        self.assertEqual(QuestionCategory.objects.count(), len(fixture("categories.json")))

    def test_no_flags_at_all_also_raises_key_error_parsons(self):
        # KNOWN-BUG: same missing --parsons argument; the command cannot even be
        # run as a no-op.
        with self.assertRaises(KeyError) as ctx:
            call_command("populate-db")
        self.assertEqual(ctx.exception.args[0], "parsons")
        self.assertEqual(QuestionCategory.objects.count(), 0)

    def test_multiple_choice_flag_raises_after_creating_questions(self):
        # KNOWN-BUG: same missing --parsons argument.
        with self.assertRaises(KeyError):
            call_command("populate-db", "--multiple-choice")
        self.assertEqual(MultipleChoiceQuestion.objects.count(), len(fixture("multiple_choice_questions.json")))

    def test_java_flag_raises_after_creating_questions(self):
        # KNOWN-BUG: same missing --parsons argument.
        with self.assertRaises(KeyError):
            call_command("populate-db", "--java")
        self.assertEqual(JavaQuestion.objects.count(), len(fixture("java_questions.json")))


class PopulateDbCommandInterfaceTests(TestCase):
    """The argparse surface, pinned separately from the behaviour."""

    def test_declared_arguments(self):
        from importlib import import_module

        module = import_module("course.management.commands.populate-db")
        command = module.Command()
        parser = command.create_parser("manage.py", "populate-db")
        options = vars(parser.parse_args([]))
        for flag in ["all", "category", "java", "multiple_choice"]:
            self.assertIn(flag, options)
            self.assertFalse(options[flag])
        # KNOWN-BUG: handle() reads options["parsons"], which argparse never sets.
        self.assertNotIn("parsons", options)

    def test_help_text(self):
        from importlib import import_module

        module = import_module("course.management.commands.populate-db")
        self.assertEqual(module.Command.help, "Populate Database with sample problems")
