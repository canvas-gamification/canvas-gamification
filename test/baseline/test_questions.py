"""Baseline tests for questions, UserQuestionJunction (UQJ) and randomisation.

Covers, against the *current* Django 3.0 / DRF 3.11 behaviour:
  * ``ensure_uqj`` fan-out invariants and the ``create_*_question(pk=...)`` update path
  * ``Question.save()`` defaults and ``Question.copy_to_event`` over polymorphic MTI
  * ``UQJ`` randomisation determinism (variables, rendered choices, Parsons lines)
  * ``get_token_value_object`` / TokenValue auto-creation on read
  * Question CRUD through the API and the exact serializer field-name sets

UPGRADE NOTE: ``get_rendered_choices`` and ``get_lines`` shuffle with the **global**
``random`` module. Where a test depends on shuffled order we assert *determinism*
(two calls with the same seed agree) plus membership/length, never a hardcoded
permutation -- CPython does not promise a stable value stream for ``random.shuffle``
across versions, so a hardcoded permutation would be a false upgrade failure.
"""

import random

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.serializers import QuestionSerializer, UQJSerializer
from course.models.java import JavaQuestion
from course.models.models import Question, QuestionCategory, TokenValue, UserQuestionJunction
from course.models.multiple_choice import MultipleChoiceQuestion
from course.models.parsons import ParsonsQuestion
from course.utils.utils import (
    create_java_question,
    create_multiple_choice_question,
    create_parsons_question,
    ensure_uqj,
    get_token_value,
    get_token_value_object,
    get_user_question_junction,
)
from test.baseline.fixtures_questions import (
    make_category,
    make_course,
    make_event,
    make_java,
    make_mcq,
    make_parsons,
    make_student,
    make_teacher,
    uqj_for,
)

SEED = 24681357


# ---------------------------------------------------------------------------
# 1. ensure_uqj
# ---------------------------------------------------------------------------


class EnsureUqjTests(TestCase):
    """course/utils/utils.py:14-44, driven by MyUser.save() and Question.save()."""

    def test_question_created_after_users_exist_fans_out_to_every_user(self):
        make_student("s1")
        make_student("s2")
        self.assertEqual(UserQuestionJunction.objects.count(), 0)

        category = make_category()
        make_mcq(category=category)
        self.assertEqual(UserQuestionJunction.objects.count(), 2)

        make_java(category=category)
        self.assertEqual(UserQuestionJunction.objects.count(), 4)

    def test_user_created_after_questions_exist_fans_out_to_every_question(self):
        category = make_category()
        make_mcq(category=category, title="q1")
        make_java(category=category, title="q2")
        make_parsons(category=category, title="q3")
        self.assertEqual(UserQuestionJunction.objects.count(), 0)

        user = make_student("s1")
        self.assertEqual(UserQuestionJunction.objects.count(), 3)
        self.assertEqual(user.question_junctions.count(), 3)

    def test_fan_out_row_count_is_users_times_questions(self):
        category = make_category()
        users = [make_student("s{}".format(i)) for i in range(3)]
        questions = [make_mcq(category=category, title="q{}".format(i)) for i in range(4)]

        self.assertEqual(UserQuestionJunction.objects.count(), 3 * 4)
        for user in users:
            self.assertEqual(user.question_junctions.count(), 4)
        for question in questions:
            self.assertEqual(question.user_junctions.count(), 3)

    def test_ensure_uqj_is_idempotent_on_resave(self):
        category = make_category()
        users = [make_student("s{}".format(i)) for i in range(2)]
        questions = [make_mcq(category=category, title="q{}".format(i)) for i in range(3)]
        expected = UserQuestionJunction.objects.count()
        self.assertEqual(expected, 6)

        for user in users:
            user.save()
        for question in questions:
            question.save()
        self.assertEqual(UserQuestionJunction.objects.count(), expected)

        # And a direct re-invocation changes nothing either.
        for user in users:
            ensure_uqj(user, None)
        for question in questions:
            ensure_uqj(None, question)
        for user in users:
            for question in questions:
                ensure_uqj(user, question)
        self.assertEqual(UserQuestionJunction.objects.count(), expected)

    def test_ensure_uqj_with_neither_argument_is_a_noop(self):
        make_student("s1")
        make_mcq(category=make_category())
        before = UserQuestionJunction.objects.count()
        self.assertIsNone(ensure_uqj(None, None))
        self.assertEqual(UserQuestionJunction.objects.count(), before)

    def test_ensure_uqj_with_both_arguments_creates_exactly_one_row(self):
        category = make_category()
        question = make_mcq(category=category)
        user = make_student("s1")
        UserQuestionJunction.objects.all().delete()

        ensure_uqj(user, question)
        self.assertEqual(UserQuestionJunction.objects.count(), 1)
        ensure_uqj(user, question)
        self.assertEqual(UserQuestionJunction.objects.count(), 1)

    def test_get_user_question_junction_is_get_or_create(self):
        category = make_category()
        question = make_mcq(category=category)
        user = make_student("s1")
        UserQuestionJunction.objects.all().delete()

        first = get_user_question_junction(user, question)
        self.assertEqual(UserQuestionJunction.objects.count(), 1)
        second = get_user_question_junction(user, question)
        self.assertEqual(second.pk, first.pk)
        self.assertEqual(UserQuestionJunction.objects.count(), 1)

    def test_uqj_unique_together_is_enforced_by_ensure_uqj(self):
        category = make_category()
        user = make_student("s1")
        question = make_mcq(category=category)
        self.assertEqual(user.question_junctions.filter(question=question).count(), 1)


class CreateQuestionUpdatePathTests(TestCase):
    """``create_*_question(pk=...)`` uses queryset.update(), bypassing save()/ensure_uqj."""

    def setUp(self):
        self.teacher = make_teacher("bl_author")
        self.category = make_category()

    def test_mcq_update_path_does_not_create_uqjs(self):
        question = create_multiple_choice_question(
            title="original",
            text="text",
            answer="a",
            author=self.teacher,
            category=self.category,
            difficulty="EASY",
            is_verified=True,
            choices={"a": "a", "b": "b"},
            visible_distractor_count=1,
        )
        self.assertIsNotNone(question)
        self.assertEqual(UserQuestionJunction.objects.count(), 1)

        UserQuestionJunction.objects.all().delete()
        result = create_multiple_choice_question(
            pk=question.pk,
            title="updated",
            text="text",
            answer="a",
            author=self.teacher,
            category=self.category,
            difficulty="EASY",
            is_verified=True,
            choices={"a": "a", "b": "b"},
            visible_distractor_count=1,
        )

        # The update path returns None and writes with .update() -> no save(), no ensure_uqj.
        self.assertIsNone(result)
        question.refresh_from_db()
        self.assertEqual(question.title, "updated")
        self.assertEqual(UserQuestionJunction.objects.count(), 0)

    def test_java_update_path_does_not_create_uqjs(self):
        create_java_question(
            title="original",
            text="text",
            author=self.teacher,
            category=self.category,
            difficulty="EASY",
            is_verified=True,
            junit_template="tpl",
            input_files=[],
        )
        question = JavaQuestion.objects.get(title="original")
        self.assertEqual(UserQuestionJunction.objects.count(), 1)

        UserQuestionJunction.objects.all().delete()
        create_java_question(
            pk=question.pk,
            title="updated",
            text="text",
            author=self.teacher,
            category=self.category,
            difficulty="EASY",
            is_verified=True,
            junit_template="tpl2",
            input_files=[],
        )
        question.refresh_from_db()
        self.assertEqual(question.title, "updated")
        self.assertEqual(question.junit_template, "tpl2")
        self.assertEqual(UserQuestionJunction.objects.count(), 0)

    def test_parsons_update_path_does_not_create_uqjs(self):
        create_parsons_question(
            title="original",
            text="text",
            author=self.teacher,
            category=self.category,
            difficulty="EASY",
            is_verified=True,
            junit_template="tpl",
            input_files=[],
        )
        question = ParsonsQuestion.objects.get(title="original")
        self.assertEqual(UserQuestionJunction.objects.count(), 1)

        UserQuestionJunction.objects.all().delete()
        create_parsons_question(
            pk=question.pk,
            title="updated",
            text="text",
            author=self.teacher,
            category=self.category,
            difficulty="EASY",
            is_verified=True,
            junit_template="tpl2",
            input_files=[],
        )
        question.refresh_from_db()
        self.assertEqual(question.title, "updated")
        self.assertEqual(UserQuestionJunction.objects.count(), 0)

    def test_create_path_returns_question_only_for_mcq(self):
        # create_multiple_choice_question returns the instance; the java/parsons
        # creators return None even on the create path.
        mcq = create_multiple_choice_question(
            title="m",
            text="t",
            answer="a",
            author=self.teacher,
            category=self.category,
            difficulty="EASY",
            is_verified=True,
            choices={"a": "a", "b": "b"},
            visible_distractor_count=1,
        )
        self.assertIsInstance(mcq, MultipleChoiceQuestion)
        self.assertIsNone(
            create_java_question(
                title="j",
                text="t",
                author=self.teacher,
                category=self.category,
                difficulty="EASY",
                is_verified=True,
                junit_template="",
                input_files=[],
            )
        )
        self.assertIsNone(
            create_parsons_question(
                title="p",
                text="t",
                author=self.teacher,
                category=self.category,
                difficulty="EASY",
                is_verified=True,
                junit_template="",
                input_files=[],
            )
        )

    def test_mcq_max_submission_allowed_defaults_to_choice_count(self):
        question = create_multiple_choice_question(
            title="m",
            text="t",
            answer="a",
            author=self.teacher,
            category=self.category,
            difficulty="EASY",
            is_verified=True,
            choices={"a": "a", "b": "b", "c": "c"},
            visible_distractor_count=1,
        )
        self.assertEqual(question.max_submission_allowed, 3)


class QuestionSaveDefaultTests(TestCase):
    """course/models/models.py:208-213."""

    def setUp(self):
        self.category = make_category()
        self.course = make_course()

    def test_practice_question_defaults_to_100_submissions(self):
        question = make_mcq(category=self.category)
        self.assertEqual(question.max_submission_allowed, 100)

    def test_assignment_question_defaults_to_100_submissions(self):
        event = make_event(self.course, name="assignment", event_type="ASSIGNMENT")
        question = make_mcq(category=self.category, event=event)
        self.assertEqual(question.max_submission_allowed, 100)

    def test_exam_question_defaults_to_10_submissions(self):
        event = make_event(self.course, name="exam", event_type="EXAM")
        question = make_mcq(category=self.category, event=event)
        self.assertEqual(question.max_submission_allowed, 10)

    def test_explicit_value_is_preserved(self):
        question = make_mcq(category=self.category, max_submission_allowed=7)
        self.assertEqual(question.max_submission_allowed, 7)


# ---------------------------------------------------------------------------
# 2. copy_to_event over polymorphic multi-table inheritance
# ---------------------------------------------------------------------------


class CopyToEventTests(TestCase):
    """course/models/models.py:229-243 -- copy.deepcopy + manual PK nulling on MTI."""

    def setUp(self):
        self.instructor = make_teacher("bl_instructor")
        self.category = make_category()
        self.course = make_course(instructor=self.instructor)
        self.event = make_event(self.course)

    def test_copying_a_java_question_yields_a_java_question(self):
        original = make_java(author=self.instructor, category=self.category, title="Original Java")
        before = JavaQuestion.objects.count()

        clone = original.copy_to_event(self.event)

        self.assertIsInstance(clone, JavaQuestion)
        self.assertEqual(JavaQuestion.objects.count(), before + 1)
        self.assertNotEqual(clone.pk, original.pk)
        self.assertIsNotNone(clone.pk)

        # Re-fetched polymorphically it is still a JavaQuestion, not a bare Question.
        refetched = Question.objects.get(pk=clone.pk)
        self.assertIsInstance(refetched, JavaQuestion)
        self.assertEqual(refetched.type_name, original.type_name)

        # Child-table payload survived the deepcopy.
        self.assertEqual(refetched.input_files, original.input_files)
        self.assertEqual(refetched.junit_template, original.junit_template)
        self.assertEqual(refetched.text, original.text)

        # Reassignment done by copy_to_event.
        self.assertEqual(refetched.title, "Original Java (Copy)")
        self.assertEqual(refetched.event_id, self.event.id)
        self.assertEqual(refetched.course_id, self.course.id)
        self.assertEqual(refetched.author_id, self.instructor.id)

        # The original is untouched.
        original.refresh_from_db()
        self.assertEqual(original.title, "Original Java")
        self.assertIsNone(original.event_id)

    def test_copy_with_explicit_title(self):
        original = make_java(author=self.instructor, category=self.category, title="Original Java")
        clone = original.copy_to_event(self.event, title="Question 3")
        self.assertEqual(clone.title, "Question 3")

    def test_copying_a_multiple_choice_question_keeps_its_class_and_choices(self):
        original = make_mcq(author=self.instructor, category=self.category, title="Original MCQ")
        clone = original.copy_to_event(self.event)

        refetched = Question.objects.get(pk=clone.pk)
        self.assertIsInstance(refetched, MultipleChoiceQuestion)
        self.assertEqual(refetched.choices, original.choices)
        self.assertEqual(refetched.answer, original.answer)
        self.assertEqual(refetched.visible_distractor_count, original.visible_distractor_count)

    def test_copying_a_parsons_question_keeps_its_class_and_input_files(self):
        original = make_parsons(author=self.instructor, category=self.category, title="Original Parsons")
        clone = original.copy_to_event(self.event)

        refetched = Question.objects.get(pk=clone.pk)
        self.assertIsInstance(refetched, ParsonsQuestion)
        self.assertEqual(refetched.input_files, original.input_files)
        self.assertEqual(refetched.junit_template, original.junit_template)

    def test_copy_fans_out_uqjs_for_the_clone(self):
        student = make_student("s1")
        original = make_java(author=self.instructor, category=self.category, title="Original Java")
        clone = original.copy_to_event(self.event)
        self.assertEqual(clone.user_junctions.count(), UserQuestionJunction.objects.filter(question=clone).count())
        self.assertTrue(student.question_junctions.filter(question=clone).exists())
        self.assertTrue(self.instructor.question_junctions.filter(question=clone).exists())


# ---------------------------------------------------------------------------
# 3. TokenValue auto-creation on read
# ---------------------------------------------------------------------------


class TokenValueAutoCreationTests(TestCase):
    """course/utils/utils.py:47-77 -- reads that write."""

    def setUp(self):
        self.parent = make_category("parent")
        self.child = make_category("child", parent=self.parent)

    def test_transient_object_when_category_is_falsy(self):
        before = TokenValue.objects.count()
        token_value = get_token_value_object(None, "EASY")
        self.assertIsNone(token_value.pk)
        self.assertEqual(token_value.value, 0)
        self.assertEqual(TokenValue.objects.count(), before)

    def test_transient_object_when_difficulty_is_falsy(self):
        before = TokenValue.objects.count()
        token_value = get_token_value_object(self.child, None)
        self.assertIsNone(token_value.pk)
        self.assertEqual(token_value.value, 0)
        self.assertEqual(TokenValue.objects.count(), before)

        token_value = get_token_value_object(self.child, "")
        self.assertIsNone(token_value.pk)
        self.assertEqual(TokenValue.objects.count(), before)

    def test_get_token_value_of_transient_object_is_zero(self):
        self.assertEqual(get_token_value(None, None), 0)

    def test_reading_a_token_value_creates_the_row(self):
        self.assertEqual(TokenValue.objects.count(), 0)
        token_value = get_token_value_object(self.child, "EASY")
        self.assertIsNotNone(token_value.pk)
        self.assertEqual(TokenValue.objects.count(), 1)

        # Second read returns the same row, no duplicate.
        again = get_token_value_object(self.child, "EASY")
        self.assertEqual(again.pk, token_value.pk)
        self.assertEqual(TokenValue.objects.count(), 1)

    def test_default_values_per_difficulty(self):
        self.assertEqual(get_token_value(self.child, "EASY"), 1)
        self.assertEqual(get_token_value(self.child, "MEDIUM"), 2)
        self.assertEqual(get_token_value(self.child, "HARD"), 3)
        self.assertEqual(TokenValue.objects.count(), 3)

    def test_question_token_value_property_creates_a_row(self):
        # KNOWN-BUG: Question.token_value is a read-only-looking property that INSERTs a
        # TokenValue row (course/models/models.py:178-180 -> course/utils/utils.py:47-59).
        # Merely serializing a question mutates the database.
        question = make_mcq(category=self.child, difficulty="MEDIUM")
        self.assertEqual(TokenValue.objects.count(), 0)
        self.assertEqual(question.token_value, 2)
        self.assertEqual(TokenValue.objects.count(), 1)


class TokenValueApiTests(APITestCase):
    def setUp(self):
        self.teacher = make_teacher("bl_teacher")
        self.parent = make_category("parent")
        self.child_a = make_category("child_a", parent=self.parent)
        self.child_b = make_category("child_b", parent=self.parent)
        self.client.force_authenticate(user=self.teacher)

    def test_get_token_values_mutates_the_database(self):
        # KNOWN-BUG: GET /api/token-values/ is a read endpoint that CREATES rows --
        # get_queryset() calls get_token_values() (course/utils/utils.py:66-77), which
        # backfills every non-root category x difficulty. Pinning the current behaviour.
        self.assertEqual(TokenValue.objects.count(), 0)

        response = self.client.get(reverse("api:token-values-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 2 non-root categories x 3 difficulties. The root category gets no rows.
        self.assertEqual(TokenValue.objects.count(), 6)
        self.assertEqual(len(response.data), 6)
        self.assertFalse(TokenValue.objects.filter(category=self.parent).exists())

    def test_repeated_get_is_idempotent_after_the_first_backfill(self):
        self.client.get(reverse("api:token-values-list"))
        self.assertEqual(TokenValue.objects.count(), 6)
        self.client.get(reverse("api:token-values-list"))
        self.assertEqual(TokenValue.objects.count(), 6)

    def test_nested_endpoint_also_creates_rows_for_root_categories(self):
        # KNOWN-BUG: GET /api/token-values/nested/ calls get_token_value_object on the
        # ROOT category too, so it creates rows get_token_values() never would.
        TokenValue.objects.all().delete()
        response = self.client.get(reverse("api:token-values-nested"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(TokenValue.objects.filter(category=self.parent).exists())

    def test_students_are_rejected(self):
        student = make_student("bl_student")
        self.client.force_authenticate(user=student)
        response = self.client.get(reverse("api:token-values-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 4. Randomisation determinism
# ---------------------------------------------------------------------------


class UqjVariableDeterminismTests(TestCase):
    """UQJ._get_variables -> generate_variables(question.variables, uqj.random_seed)."""

    VARIABLE_SCHEMA = [
        {"name": "a", "type": "int", "min": 1, "max": 100},
        {"name": "b", "type": "enum", "values": ["x", "y", "z"]},
    ]

    def setUp(self):
        self.category = make_category()
        self.user_one = make_student("s1")
        self.user_two = make_student("s2")
        self.question = make_mcq(category=self.category, variables=self.VARIABLE_SCHEMA)

    def test_same_uqj_returns_the_same_variables_every_time(self):
        uqj = uqj_for(self.user_one, self.question, random_seed=SEED)
        first = uqj.get_variables()
        second = uqj.get_variables()
        self.assertEqual(first, second)
        self.assertEqual(sorted(first.keys()), ["a", "b"])

    def test_two_uqjs_with_the_same_seed_agree(self):
        one = uqj_for(self.user_one, self.question, random_seed=SEED)
        two = uqj_for(self.user_two, self.question, random_seed=SEED)
        self.assertEqual(one.get_variables(), two.get_variables())

    def test_variables_are_in_range(self):
        uqj = uqj_for(self.user_one, self.question, random_seed=SEED)
        variables = uqj.get_variables()
        self.assertGreaterEqual(variables["a"], 1)
        self.assertLessEqual(variables["a"], 100)
        self.assertIn(variables["b"], ["x", "y", "z"])

    def test_no_errors_for_a_valid_schema(self):
        uqj = uqj_for(self.user_one, self.question, random_seed=SEED)
        self.assertEqual(uqj.get_variables_errors(), [])

    def test_non_variable_question_returns_empty(self):
        # Question (the base polymorphic model) is not a VariableQuestion.
        question = Question(title="plain", text="plain text", category=self.category)
        question.save()
        uqj = uqj_for(self.user_one, question)
        self.assertEqual(uqj.get_variables(), {})
        self.assertEqual(uqj.get_variables_errors(), [])

    def test_string_schema_is_reported_as_an_invalid_schema(self):
        # KNOWN-BUG-ADJACENT: a JSON *string* schema (which the repo's own fixtures in
        # test/questions.py pass as variables="[]") silently produces no variables and
        # an "Invalid schema type." error rather than being parsed.
        question = make_mcq(category=self.category, title="string schema", variables="[]")
        uqj = uqj_for(self.user_one, question)
        self.assertEqual(uqj.get_variables(), {})
        self.assertEqual(uqj.get_variables_errors(), ["Invalid schema type."])

    def test_rendered_text_substitutes_variables(self):
        question = make_mcq(
            category=self.category,
            title="rendered",
            text="value is {{a}}",
            variables=[{"name": "a", "type": "int", "min": 42, "max": 42}],
        )
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        self.assertEqual(uqj.get_rendered_text(), "value is 42")


class RenderedChoicesTests(TestCase):
    """course/models/models.py:346-359 -- truncation + shuffle with the GLOBAL random."""

    def setUp(self):
        self.category = make_category()
        self.user_one = make_student("s1")
        self.user_two = make_student("s2")

    def make_question(self, **kwargs):
        return make_mcq(category=self.category, **kwargs)

    def test_truncation_to_visible_distractor_count_plus_answers(self):
        question = self.make_question(answer="a", visible_distractor_count=2)
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        rendered = uqj.get_rendered_choices()
        self.assertEqual(len(rendered), 3)
        self.assertEqual(set(rendered.keys()), {"a", "b", "c"})

    def test_truncation_with_multiple_answers(self):
        question = self.make_question(answer="a,b", visible_distractor_count=2, title="multi")
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        rendered = uqj.get_rendered_choices()
        self.assertEqual(len(rendered), 4)
        self.assertEqual(set(rendered.keys()), {"a", "b", "c", "d"})

    def test_truncation_with_zero_distractors(self):
        question = self.make_question(answer="a", visible_distractor_count=0, title="zero")
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        self.assertEqual(set(uqj.get_rendered_choices().keys()), {"a"})

    def test_truncation_beyond_available_choices_returns_everything(self):
        question = self.make_question(
            answer="a", visible_distractor_count=99, choices={"a": "A", "b": "B"}, title="over"
        )
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        self.assertEqual(set(uqj.get_rendered_choices().keys()), {"a", "b"})

    def test_calling_twice_yields_the_same_result_and_ordering(self):
        question = self.make_question(answer="a", visible_distractor_count=4)
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        first = uqj.get_rendered_choices()
        second = uqj.get_rendered_choices()
        self.assertEqual(first, second)
        # Ordering compared run-to-run, not against a hardcoded permutation.
        self.assertEqual(list(first.keys()), list(second.keys()))

    def test_same_seed_across_users_yields_the_same_ordering(self):
        question = self.make_question(answer="a", visible_distractor_count=4)
        one = uqj_for(self.user_one, question, random_seed=SEED)
        two = uqj_for(self.user_two, question, random_seed=SEED)
        self.assertEqual(list(one.get_rendered_choices().keys()), list(two.get_rendered_choices().keys()))

    def test_result_is_independent_of_the_global_random_state(self):
        # get_rendered_choices re-seeds the global `random` module on every call, so
        # unrelated random usage in between must not perturb it. This is what makes the
        # test independent of execution order.
        question = self.make_question(answer="a", visible_distractor_count=4)
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        random.seed(1)
        expected = list(uqj.get_rendered_choices().keys())
        random.seed(999999)
        for _ in range(17):
            random.random()
        self.assertEqual(list(uqj.get_rendered_choices().keys()), expected)

    def test_rendered_choices_carry_the_choice_bodies(self):
        question = self.make_question(answer="a", visible_distractor_count=2)
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        rendered = uqj.get_rendered_choices()
        self.assertEqual(rendered["a"], "alpha")
        self.assertEqual(rendered["b"], "bravo")
        self.assertEqual(rendered["c"], "charlie")

    def test_choice_bodies_are_rendered_with_the_variables(self):
        question = self.make_question(
            title="vars",
            answer="a",
            visible_distractor_count=1,
            choices={"a": "n={{n}}", "b": "other"},
            variables=[{"name": "n", "type": "int", "min": 5, "max": 5}],
        )
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        self.assertEqual(uqj.get_rendered_choices()["a"], "n=5")

    def test_json_string_choices_are_parsed(self):
        question = self.make_question(
            title="strchoices", answer="a", visible_distractor_count=1, choices='{"a": "A", "b": "B"}'
        )
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        self.assertEqual(set(uqj.get_rendered_choices().keys()), {"a", "b"})

    def test_non_mcq_returns_empty_dict(self):
        question = make_java(category=self.category, title="java")
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        self.assertEqual(uqj.get_rendered_choices(), {})


class ParsonsLineTests(TestCase):
    """course/models/models.py:361-374 -- Parsons line shuffling."""

    def setUp(self):
        self.category = make_category()
        self.user_one = make_student("s1")
        self.user_two = make_student("s2")
        self.question = make_parsons(category=self.category)

    def test_shape_is_a_list_of_name_and_lines(self):
        uqj = uqj_for(self.user_one, self.question, random_seed=SEED)
        lines = uqj.get_lines()
        self.assertIsInstance(lines, list)
        self.assertEqual(len(lines), 2)
        self.assertEqual(sorted(lines[0].keys()), ["lines", "name"])
        self.assertEqual([f["name"] for f in lines], ["Main.java", "Second.java"])

    def test_all_lines_are_preserved_only_reordered(self):
        uqj = uqj_for(self.user_one, self.question, random_seed=SEED)
        lines = uqj.get_lines()
        self.assertEqual(
            sorted(lines[0]["lines"]), sorted(["line one", "line two", "line three", "line four", "line five"])
        )
        self.assertEqual(len(lines[1]["lines"]), 4)

    def test_calling_twice_yields_the_same_ordering(self):
        uqj = uqj_for(self.user_one, self.question, random_seed=SEED)
        first = uqj.get_lines()
        second = uqj.get_lines()
        self.assertEqual(first, second)

    def test_same_seed_across_users_yields_the_same_ordering(self):
        one = uqj_for(self.user_one, self.question, random_seed=SEED)
        two = uqj_for(self.user_two, self.question, random_seed=SEED)
        self.assertEqual(one.get_lines(), two.get_lines())

    def test_result_is_independent_of_the_global_random_state(self):
        uqj = uqj_for(self.user_one, self.question, random_seed=SEED)
        random.seed(7)
        expected = uqj.get_lines()
        random.seed(31337)
        for _ in range(11):
            random.random()
        self.assertEqual(uqj.get_lines(), expected)

    def test_lines_are_rendered_with_the_variables(self):
        question = make_parsons(
            category=self.category,
            title="parsons vars",
            variables=[{"name": "n", "type": "int", "min": 8, "max": 8}],
            input_files=[{"name": "F{{n}}.java", "compile": True, "lines": ["a={{n}}"]}],
        )
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        lines = uqj.get_lines()
        self.assertEqual(lines[0]["name"], "F8.java")
        self.assertEqual(lines[0]["lines"], ["a=8"])

    def test_non_parsons_returns_empty_dict(self):
        # Note the asymmetry with the list returned for Parsons questions.
        question = make_mcq(category=self.category, title="mcq")
        uqj = uqj_for(self.user_one, question, random_seed=SEED)
        self.assertEqual(uqj.get_lines(), {})


class UqjInputFileTests(TestCase):
    """course/models/models.py:376-394."""

    def setUp(self):
        self.category = make_category()
        self.user = make_student("s1")

    def test_java_input_files_are_rendered(self):
        question = make_java(
            category=self.category,
            variables=[{"name": "n", "type": "int", "min": 3, "max": 3}],
            input_files=[{"name": "F{{n}}.java", "compile": True, "template": "// {{n}}", "hidden": False}],
        )
        uqj = uqj_for(self.user, question, random_seed=SEED)
        files = uqj.get_input_files()
        self.assertEqual(files[0]["name"], "F3.java")
        self.assertEqual(files[0]["template"], "// 3")
        self.assertEqual(uqj.get_input_file_names(), "F3.java")
        self.assertTrue(uqj.should_compile("F3.java"))
        self.assertFalse(uqj.should_compile("Nope.java"))

    def test_only_compilable_files_are_named(self):
        question = make_java(category=self.category, title="two files")
        uqj = uqj_for(self.user, question, random_seed=SEED)
        self.assertEqual(uqj.get_input_file_names(), "Main.java")

    def test_mcq_has_no_input_files(self):
        question = make_mcq(category=self.category)
        uqj = uqj_for(self.user, question, random_seed=SEED)
        self.assertEqual(uqj.get_input_files(), [])


# ---------------------------------------------------------------------------
# 5. Serializer field-name sets
# ---------------------------------------------------------------------------


QUESTION_SERIALIZER_FIELDS = {
    "id",
    "title",
    "text",
    "max_submission_allowed",
    "time_created",
    "time_modified",
    "author",
    "author_name",
    "difficulty",
    "is_verified",
    "token_value",
    "type_name",
    "event",
    "event_obj",
    "category",
    "parent_category_name",
    "full_category_name",
    "category_name",
    "course",
    "status",
    "is_sample",
    "is_open",
    "is_exam",
    "is_exam_and_open",
    "is_author",
    "is_practice",
}

UQJ_SERIALIZER_FIELDS = {
    "id",
    "last_viewed",
    "opened_tutorial",
    "tokens_received",
    "is_solved",
    "is_partially_solved",
    "question",
    "question_id",
    "num_attempts",
    "status",
    "formatted_current_tokens_received",
    "is_allowed_to_submit",
    "variables",
    "variables_errors",
    "rendered_text",
    "rendered_choices",
    "rendered_lines",
    "input_files",
    "is_checkbox",
    "report",
    "is_favorite",
}

MCQ_SERIALIZER_FIELDS = {
    "id",
    "title",
    "text",
    "answer",
    "max_submission_allowed",
    "time_created",
    "time_modified",
    "author",
    "category",
    "category_obj",
    "difficulty",
    "is_verified",
    "variables",
    "variation_types",
    "choices",
    "type_name",
    "visible_distractor_count",
    "token_value",
    "event",
    "event_obj",
    "is_sample",
    "parent_category_name",
    "course",
    "author_name",
    "is_checkbox",
}

JAVA_SERIALIZER_FIELDS = {
    "id",
    "title",
    "text",
    "answer",
    "max_submission_allowed",
    "time_created",
    "time_modified",
    "author",
    "category",
    "category_obj",
    "difficulty",
    "is_verified",
    "variables",
    "variation_types",
    "junit_template",
    "input_files",
    "token_value",
    "type_name",
    "event",
    "event_obj",
    "is_sample",
    "parent_category_name",
    "course",
    "author_name",
}

PARSONS_SERIALIZER_FIELDS = JAVA_SERIALIZER_FIELDS | {"category_name", "event_name"}


class SerializerFieldSetTests(TestCase):
    """Field-name drift is the most common silent DRF-upgrade regression."""

    def test_question_serializer_fields(self):
        self.assertEqual(set(QuestionSerializer().fields.keys()), QUESTION_SERIALIZER_FIELDS)

    def test_uqj_serializer_fields(self):
        self.assertEqual(set(UQJSerializer().fields.keys()), UQJ_SERIALIZER_FIELDS)

    def test_uqj_serializer_nests_the_question_serializer(self):
        nested = UQJSerializer().fields["question"]
        self.assertEqual(set(nested.fields.keys()), QUESTION_SERIALIZER_FIELDS)
        self.assertTrue(nested.read_only)


class QuestionApiSerializerOutputTests(APITestCase):
    def setUp(self):
        self.teacher = make_teacher("bl_teacher")
        self.category = make_category()
        self.question = make_mcq(author=self.teacher, category=self.category)
        self.client.force_authenticate(user=self.teacher)

    def test_question_list_payload_keys(self):
        response = self.client.get(reverse("api:question-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {"count", "next", "previous", "results"})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(set(response.data["results"][0].keys()), QUESTION_SERIALIZER_FIELDS)

    def test_question_detail_uses_the_type_specific_serializer(self):
        url = reverse("api:question-detail", kwargs={"pk": self.question.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), MCQ_SERIALIZER_FIELDS)

    def test_uqj_list_payload_keys(self):
        response = self.client.get(reverse("api:uqj-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(set(response.data["results"][0].keys()), UQJ_SERIALIZER_FIELDS)
        self.assertEqual(set(response.data["results"][0]["question"].keys()), QUESTION_SERIALIZER_FIELDS)

    def test_uqj_list_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("api:uqj-list"))
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_count_favorite_action(self):
        # NB: the route is /count-favorite/ but DRF derives the *url name* from the
        # method name (get_favorite_count), not from url_path.
        url = reverse("api:question-get-favorite-count", kwargs={"pk": self.question.pk})
        self.assertEqual(self.client.get(url).data, 0)

        uqj = uqj_for(self.teacher, self.question)
        uqj.is_favorite = True
        uqj.save()
        self.assertEqual(self.client.get(url).data, 1)


# ---------------------------------------------------------------------------
# 6. Question CRUD through the API
# ---------------------------------------------------------------------------


class MultipleChoiceQuestionCrudTests(APITestCase):
    def setUp(self):
        self.teacher = make_teacher("bl_teacher")
        self.category = make_category()
        self.client.force_authenticate(user=self.teacher)

    def payload(self, **overrides):
        data = {
            "title": "API MCQ",
            "text": "What is 1 + 1?",
            "answer": "a",
            "difficulty": "EASY",
            "visible_distractor_count": 1,
            "choices": {"a": "2", "b": "3"},
            "variables": [],
            "category": self.category.id,
        }
        data.update(overrides)
        return data

    def test_create(self):
        response = self.client.post(reverse("api:multiple-choice-question-list"), self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), MCQ_SERIALIZER_FIELDS)

        question = MultipleChoiceQuestion.objects.get(title="API MCQ")
        self.assertEqual(question.author_id, self.teacher.id)
        self.assertEqual(question.choices, {"a": "2", "b": "3"})
        self.assertEqual(question.visible_distractor_count, 1)
        self.assertFalse(question.is_verified)
        self.assertEqual(question.question_status, Question.CREATED)
        # Question.save() defaults max_submission_allowed for a practice question.
        self.assertEqual(question.max_submission_allowed, 100)
        # ensure_uqj ran on save.
        self.assertEqual(question.user_junctions.count(), 1)

    def test_create_requires_the_mandatory_fields(self):
        response = self.client.post(reverse("api:multiple-choice-question-list"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ["title", "text", "difficulty", "answer", "visible_distractor_count", "choices", "variables"]:
            self.assertIn(field, response.data)

    def test_update(self):
        question = make_mcq(author=self.teacher, category=self.category, title="before")
        url = reverse("api:multiple-choice-question-detail", kwargs={"pk": question.pk})

        response = self.client.patch(url, {"title": "after"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        question.refresh_from_db()
        self.assertEqual(question.title, "after")

    def test_full_update(self):
        question = make_mcq(author=self.teacher, category=self.category, title="before")
        url = reverse("api:multiple-choice-question-detail", kwargs={"pk": question.pk})

        response = self.client.put(url, self.payload(title="replaced"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        question.refresh_from_db()
        self.assertEqual(question.title, "replaced")
        self.assertEqual(question.choices, {"a": "2", "b": "3"})

    def test_delete_is_a_hard_delete_on_the_typed_viewset(self):
        question = make_mcq(author=self.teacher, category=self.category, title="doomed")
        url = reverse("api:multiple-choice-question-detail", kwargs={"pk": question.pk})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MultipleChoiceQuestion.objects.filter(pk=question.pk).exists())
        self.assertFalse(Question.objects.filter(pk=question.pk).exists())
        self.assertEqual(UserQuestionJunction.objects.filter(question_id=question.pk).count(), 0)

    def test_anonymous_access_is_rejected(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(reverse("api:multiple-choice-question-list"), self.payload(), format="json")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class JavaQuestionCrudTests(APITestCase):
    def setUp(self):
        self.teacher = make_teacher("bl_teacher")
        self.category = make_category()
        self.client.force_authenticate(user=self.teacher)

    def payload(self, **overrides):
        data = {
            "title": "API Java",
            "text": "Write a class",
            "difficulty": "MEDIUM",
            "junit_template": "public class MainTest {}",
            "input_files": [{"name": "Main.java", "compile": True, "template": "", "hidden": False}],
            "variables": [],
            "category": self.category.id,
        }
        data.update(overrides)
        return data

    def test_create(self):
        response = self.client.post(reverse("api:java-question-list"), self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), JAVA_SERIALIZER_FIELDS)

        question = JavaQuestion.objects.get(title="API Java")
        self.assertEqual(question.author_id, self.teacher.id)
        self.assertEqual(question.junit_template, "public class MainTest {}")
        self.assertEqual(question.input_files[0]["name"], "Main.java")
        self.assertEqual(question.max_submission_allowed, 100)
        self.assertEqual(question.user_junctions.count(), 1)

    def test_create_requires_junit_template_and_input_files(self):
        response = self.client.post(reverse("api:java-question-list"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ["title", "text", "difficulty", "junit_template", "input_files", "variables"]:
            self.assertIn(field, response.data)

    def test_update(self):
        question = make_java(author=self.teacher, category=self.category, title="before")
        url = reverse("api:java-question-detail", kwargs={"pk": question.pk})

        response = self.client.patch(url, {"junit_template": "changed"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        question.refresh_from_db()
        self.assertEqual(question.junit_template, "changed")

    def test_delete(self):
        question = make_java(author=self.teacher, category=self.category, title="doomed")
        url = reverse("api:java-question-detail", kwargs={"pk": question.pk})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(JavaQuestion.objects.filter(pk=question.pk).exists())


class ParsonsQuestionCrudTests(APITestCase):
    def setUp(self):
        self.teacher = make_teacher("bl_teacher")
        self.category = make_category()
        self.client.force_authenticate(user=self.teacher)

    def payload(self, **overrides):
        data = {
            "title": "API Parsons",
            "text": "Order the lines",
            "difficulty": "HARD",
            "junit_template": "public class MainTest {}",
            "input_files": [{"name": "Main.java", "compile": True, "lines": ["a", "b", "c"]}],
            "variables": [],
            "category": self.category.id,
        }
        data.update(overrides)
        return data

    def test_create(self):
        response = self.client.post(reverse("api:parsons-question-list"), self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), PARSONS_SERIALIZER_FIELDS)

        question = ParsonsQuestion.objects.get(title="API Parsons")
        self.assertEqual(question.author_id, self.teacher.id)
        self.assertEqual(question.input_files[0]["lines"], ["a", "b", "c"])
        self.assertEqual(question.max_submission_allowed, 100)
        self.assertEqual(question.user_junctions.count(), 1)

    def test_create_requires_the_mandatory_fields(self):
        response = self.client.post(reverse("api:parsons-question-list"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ["title", "text", "difficulty", "junit_template", "input_files", "variables"]:
            self.assertIn(field, response.data)

    def test_update(self):
        question = make_parsons(author=self.teacher, category=self.category, title="before")
        url = reverse("api:parsons-question-detail", kwargs={"pk": question.pk})

        response = self.client.patch(url, {"title": "after"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        question.refresh_from_db()
        self.assertEqual(question.title, "after")

    def test_delete(self):
        question = make_parsons(author=self.teacher, category=self.category, title="doomed")
        url = reverse("api:parsons-question-detail", kwargs={"pk": question.pk})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ParsonsQuestion.objects.filter(pk=question.pk).exists())


class QuestionViewSetSoftDeleteTests(APITestCase):
    """DELETE /api/questions/{pk}/ is a soft delete returning 200 with the object."""

    def setUp(self):
        self.teacher = make_teacher("bl_teacher")
        self.category = make_category()
        self.question = make_mcq(author=self.teacher, category=self.category, title="soft")
        self.client.force_authenticate(user=self.teacher)

    def test_soft_delete_keeps_the_row(self):
        url = reverse("api:question-detail", kwargs={"pk": self.question.pk})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.question.refresh_from_db()
        self.assertEqual(self.question.question_status, Question.DELETED)
        self.assertTrue(Question.objects.filter(pk=self.question.pk).exists())
        self.assertEqual(set(response.data.keys()), MCQ_SERIALIZER_FIELDS)

    def test_soft_deleted_questions_disappear_from_the_list(self):
        self.client.delete(reverse("api:question-detail", kwargs={"pk": self.question.pk}))
        response = self.client.get(reverse("api:question-list"))
        self.assertEqual(response.data["count"], 0)

    def test_model_level_soft_delete(self):
        event = make_event(make_course(instructor=self.teacher))
        question = make_mcq(author=self.teacher, category=self.category, event=event, title="detached")

        question.soft_delete()

        question.refresh_from_db()
        self.assertIsNone(question.event_id)
        self.assertFalse(question.is_verified)
        self.assertEqual(question.question_status, Question.DELETED)


class QuestionListFilterTests(APITestCase):
    def setUp(self):
        self.teacher = make_teacher("bl_teacher")
        self.category = make_category()
        self.easy = make_mcq(author=self.teacher, category=self.category, title="Easy One", difficulty="EASY")
        self.hard = make_mcq(author=self.teacher, category=self.category, title="Hard One", difficulty="HARD")
        self.client.force_authenticate(user=self.teacher)

    def test_filter_by_difficulty(self):
        response = self.client.get(reverse("api:question-list"), {"difficulty": "HARD"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.hard.id)

    def test_search_by_title(self):
        response = self.client.get(reverse("api:question-list"), {"search": "Easy"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.easy.id)

    def test_ordering_by_title(self):
        response = self.client.get(reverse("api:question-list"), {"ordering": "-title"})
        titles = [row["title"] for row in response.data["results"]]
        self.assertEqual(titles, ["Hard One", "Easy One"])

    def test_download_questions_returns_a_plain_list(self):
        response = self.client.get(reverse("api:question-download-questions"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)

    def test_students_still_see_every_question(self):
        # KNOWN-BUG: QuestionViewSet.get_queryset (api/views/question.py:64-69) discards
        # the result of `queryset.filter(author=user)` for non-teachers, so students see
        # all questions instead of only their own. Pinning the current behaviour.
        student = make_student("bl_student")
        self.client.force_authenticate(user=student)
        response = self.client.get(reverse("api:question-list"))
        self.assertEqual(response.data["count"], 2)


class QuestionCategoryHelperTests(TestCase):
    """A couple of QuestionCategory invariants the question tests depend on."""

    def test_question_count_of_a_root_category_ignores_its_own_questions(self):
        parent = make_category("parent")
        child = make_category("child", parent=parent)
        make_mcq(category=parent, title="on the parent")
        make_mcq(category=child, title="on the child")

        # KNOWN-BUG: a root category reports only its children's questions, never its own
        # (course/models/models.py:53-60).
        self.assertEqual(QuestionCategory.objects.get(pk=parent.pk).question_count, 1)
        self.assertEqual(QuestionCategory.objects.get(pk=child.pk).question_count, 1)

    def test_full_name_includes_the_parent(self):
        parent = make_category("parent")
        child = make_category("child", parent=parent)
        self.assertEqual(child.full_name, "parent :: child")
        self.assertEqual(parent.full_name, "parent")
