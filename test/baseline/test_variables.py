"""Baseline tests for course/utils/variables.py -- the question randomisation engine.

Locks in the behaviour of ``evaluate`` (the expression sandbox), ``render_text`` and
``generate_variables`` (the 5 variable types + the 3 error paths) so that the
Python 3.14 / Django 6.0 upgrade can be verified behaviour-preserving.

Portability notes for the upgrade:
  * These tests never assert an exact pseudo-random *value* produced by
    ``random.Random(seed)``: CPython does not guarantee the value stream of
    ``randrange``/``uniform`` across versions. Instead we assert (a) determinism --
    two calls with the same seed agree -- and (b) membership/range of the result.
  * Error strings asserted here are the application's own messages
    (``course/utils/variables.py``), never Django/DRF internals.
"""

from django.test import SimpleTestCase

from course.utils.variables import ALLOWED_NAMES, evaluate, generate_variables, render_text

SEED = 12345


class EvaluateSandboxTests(SimpleTestCase):
    """course/utils/variables.py:22-30 -- the expression sandbox."""

    def assert_name_rejected(self, expression, name):
        with self.assertRaises(NameError) as ctx:
            evaluate(expression)
        # Our own message, not a Python/Django internal one.
        self.assertEqual(str(ctx.exception), "The use of '{}' is not allowed".format(name))

    def test_import_is_rejected(self):
        self.assert_name_rejected("__import__('os')", "__import__")

    def test_open_is_rejected(self):
        self.assert_name_rejected("open('/etc/passwd')", "open")

    def test_eval_is_rejected(self):
        self.assert_name_rejected("eval('1+1')", "eval")

    def test_exec_is_rejected(self):
        self.assert_name_rejected("exec('x=1')", "exec")

    def test_dunder_attribute_access_is_rejected(self):
        # Attribute names land in co_names too, which is what blocks the classic
        # ().__class__.__bases__[0].__subclasses__() sandbox escape.
        self.assert_name_rejected("().__class__", "__class__")

    def test_dunder_subclasses_escape_is_rejected(self):
        self.assert_name_rejected("().__class__.__bases__[0].__subclasses__()", "__class__")

    def test_globals_is_rejected(self):
        self.assert_name_rejected("globals()", "globals")

    def test_unknown_name_is_rejected(self):
        self.assert_name_rejected("some_random_name", "some_random_name")

    def test_math_names_are_allowed(self):
        self.assertEqual(evaluate("sqrt(16)"), 4.0)
        self.assertEqual(evaluate("floor(3.7)"), 3)
        self.assertEqual(evaluate("pow(2, 10)"), 1024.0)
        self.assertAlmostEqual(evaluate("pi"), 3.141592653589793)

    def test_str_method_names_are_allowed(self):
        # STR_NAMES exposes the unbound str methods, e.g. str.upper as "upper".
        self.assertEqual(evaluate("upper('abc')"), "ABC")
        self.assertEqual(evaluate("join(',', ['a', 'b'])"), "a,b")

    def test_builtin_allowlist_names_work(self):
        self.assertEqual(evaluate("len('abcd')"), 4)
        self.assertEqual(evaluate("round(3.14159, 2)"), 3.14)
        self.assertEqual(evaluate("chr(65)"), "A")
        self.assertEqual(evaluate("int('42')"), 42)
        self.assertEqual(evaluate("str(42)"), "42")
        self.assertEqual(evaluate("list('ab')"), ["a", "b"])
        self.assertEqual(evaluate("dict()"), {})
        self.assertEqual(evaluate("set()"), set())

    def test_literals_and_arithmetic_need_no_names(self):
        self.assertEqual(evaluate("1 + 2 * 3"), 7)
        self.assertEqual(evaluate("None"), None)
        self.assertEqual(evaluate("[1, 2][1]"), 2)

    def test_syntax_error_propagates(self):
        # compile() failures are not converted; generate_variables catches them instead.
        with self.assertRaises(SyntaxError):
            evaluate("1 +")

    def test_allowed_names_contains_expected_builtins(self):
        for name in ["len", "round", "chr", "str", "int", "list", "dict", "set"]:
            self.assertIn(name, ALLOWED_NAMES)
        for name in ["__import__", "open", "eval", "exec", "globals", "getattr", "__builtins__"]:
            self.assertNotIn(name, ALLOWED_NAMES)


class RenderTextTests(SimpleTestCase):
    """course/utils/variables.py:32-36."""

    def test_replaces_double_brace_placeholders(self):
        self.assertEqual(render_text("x is {{x}}", {"x": 5}), "x is 5")

    def test_replaces_every_occurrence(self):
        self.assertEqual(render_text("{{x}}{{x}}", {"x": "a"}), "aa")

    def test_unknown_placeholder_is_left_untouched(self):
        self.assertEqual(render_text("{{y}}", {"x": 1}), "{{y}}")

    def test_non_string_input_is_coerced(self):
        self.assertEqual(render_text(None, {}), "None")
        self.assertEqual(render_text(7, {}), "7")

    def test_values_are_stringified(self):
        self.assertEqual(render_text("{{v}}", {"v": [1, 2]}), "[1, 2]")


class GenerateVariablesTypeTests(SimpleTestCase):
    """course/utils/variables.py:39-93 -- one test per variable type."""

    def test_int_type(self):
        variables, errors = generate_variables([{"name": "x", "type": "int", "min": 5, "max": 10}], SEED)
        self.assertEqual(errors, [])
        self.assertEqual(list(variables.keys()), ["x"])
        self.assertIsInstance(variables["x"], int)
        # randrange(min, max + 1) -> max is inclusive.
        self.assertGreaterEqual(variables["x"], 5)
        self.assertLessEqual(variables["x"], 10)

    def test_int_type_with_degenerate_range_is_exact(self):
        variables, errors = generate_variables([{"name": "x", "type": "int", "min": 3, "max": 3}], SEED)
        self.assertEqual(errors, [])
        self.assertEqual(variables, {"x": 3})

    def test_int_bounds_are_evaluated_expressions(self):
        variables, errors = generate_variables(
            [{"name": "x", "type": "int", "min": "floor(2.9)", "max": "floor(2.9)"}], SEED
        )
        self.assertEqual(errors, [])
        self.assertEqual(variables, {"x": 2})

    def test_float_type(self):
        variables, errors = generate_variables(
            [{"name": "y", "type": "float", "min": 0, "max": 1, "precision": 2}], SEED
        )
        self.assertEqual(errors, [])
        self.assertIsInstance(variables["y"], float)
        # uniform(min, max + 1) then floor-truncated to `precision` decimal places.
        self.assertGreaterEqual(variables["y"], 0)
        self.assertLessEqual(variables["y"], 2)
        self.assertEqual(round(variables["y"] * 100), variables["y"] * 100)

    def test_float_without_precision_is_an_error(self):
        # precision defaults to None -> evaluate("None") -> 10 ** None -> TypeError,
        # which generate_variables swallows into the errors list.
        variables, errors = generate_variables([{"name": "y", "type": "float", "min": 0, "max": 1}], SEED)
        self.assertEqual(variables, {})
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("y: "))

    def test_enum_type(self):
        values = ["red", "green", "blue"]
        variables, errors = generate_variables([{"name": "c", "type": "enum", "values": values}], SEED)
        self.assertEqual(errors, [])
        self.assertIn(variables["c"], values)

    def test_enum_values_are_rendered_with_earlier_variables(self):
        schema = [
            {"name": "n", "type": "int", "min": 4, "max": 4},
            {"name": "c", "type": "enum", "values": ["v{{n}}"]},
        ]
        variables, errors = generate_variables(schema, SEED)
        self.assertEqual(errors, [])
        self.assertEqual(variables["c"], "v4")

    def test_expression_type(self):
        variables, errors = generate_variables(
            [
                {"name": "a", "type": "int", "min": 2, "max": 2},
                {"name": "b", "type": "expression", "expression": "{{a}} * 10 + len('xyz')"},
            ],
            SEED,
        )
        self.assertEqual(errors, [])
        self.assertEqual(variables["b"], 23)

    def test_expression_type_uses_the_sandbox(self):
        variables, errors = generate_variables(
            [{"name": "b", "type": "expression", "expression": "__import__('os').getcwd()"}], SEED
        )
        self.assertEqual(variables, {})
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("b: "))
        self.assertIn("is not allowed", errors[0])

    def test_choice_type(self):
        variables, errors = generate_variables(
            [{"name": "p", "type": "choice", "values": ["zero", "one", "two"], "choice": 1}], SEED
        )
        self.assertEqual(errors, [])
        self.assertEqual(variables["p"], "one")

    def test_choice_index_is_an_evaluated_expression(self):
        variables, errors = generate_variables(
            [
                {"name": "i", "type": "int", "min": 2, "max": 2},
                {"name": "p", "type": "choice", "values": ["zero", "one", "two"], "choice": "{{i}}"},
            ],
            SEED,
        )
        self.assertEqual(errors, [])
        self.assertEqual(variables["p"], "two")

    def test_choice_out_of_range_becomes_an_error(self):
        variables, errors = generate_variables([{"name": "p", "type": "choice", "values": ["only"], "choice": 5}], SEED)
        self.assertEqual(variables, {})
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("p: "))

    def test_unknown_type_is_silently_ignored(self):
        # No `else` branch in _generate_variable: an unknown type produces neither a
        # variable nor an error.
        variables, errors = generate_variables([{"name": "z", "type": "nope"}], SEED)
        self.assertEqual(variables, {})
        self.assertEqual(errors, [])

    def test_missing_type_is_silently_ignored(self):
        variables, errors = generate_variables([{"name": "z"}], SEED)
        self.assertEqual(variables, {})
        self.assertEqual(errors, [])

    def test_all_five_types_together(self):
        schema = [
            {"name": "i", "type": "int", "min": 1, "max": 1},
            {"name": "f", "type": "float", "min": 0, "max": 0, "precision": 3},
            {"name": "e", "type": "enum", "values": ["only"]},
            {"name": "x", "type": "expression", "expression": "{{i}} + 1"},
            {"name": "c", "type": "choice", "values": ["a", "b"], "choice": 0},
        ]
        variables, errors = generate_variables(schema, SEED)
        self.assertEqual(errors, [])
        self.assertEqual(sorted(variables.keys()), ["c", "e", "f", "i", "x"])
        self.assertEqual(variables["i"], 1)
        self.assertEqual(variables["e"], "only")
        self.assertEqual(variables["x"], 2)
        self.assertEqual(variables["c"], "a")


class GenerateVariablesErrorTests(SimpleTestCase):
    """course/utils/variables.py:64-93 -- the three schema-level error paths."""

    def test_missing_name(self):
        variables, errors = generate_variables([{"type": "int", "min": 1, "max": 2}], SEED)
        self.assertEqual(variables, {})
        self.assertEqual(errors, ["Name was not defined for a variable!"])

    def test_duplicate_name(self):
        schema = [
            {"name": "x", "type": "int", "min": 1, "max": 1},
            {"name": "x", "type": "int", "min": 9, "max": 9},
        ]
        variables, errors = generate_variables(schema, SEED)
        self.assertEqual(errors, ["Duplicate variable name detected!"])
        # First definition wins; the duplicate is skipped, not overwritten.
        self.assertEqual(variables, {"x": 1})

    def test_non_list_schema_string(self):
        self.assertEqual(generate_variables("[]", SEED), ({}, ["Invalid schema type."]))

    def test_non_list_schema_dict(self):
        self.assertEqual(generate_variables({"name": "x", "type": "int"}, SEED), ({}, ["Invalid schema type."]))

    def test_non_list_schema_none(self):
        self.assertEqual(generate_variables(None, SEED), ({}, ["Invalid schema type."]))

    def test_empty_list_schema(self):
        self.assertEqual(generate_variables([], SEED), ({}, []))

    def test_errors_do_not_abort_later_variables(self):
        schema = [
            {"name": "bad", "type": "expression", "expression": "open('x')"},
            {"name": "good", "type": "int", "min": 7, "max": 7},
        ]
        variables, errors = generate_variables(schema, SEED)
        self.assertEqual(len(errors), 1)
        self.assertEqual(variables, {"good": 7})


class GenerateVariablesDeterminismTests(SimpleTestCase):
    """The determinism contract that question randomisation relies on.

    UPGRADE NOTE: we compare two runs against each other rather than against a
    hardcoded value, because CPython does not promise a stable value stream from
    ``Random.randrange``/``Random.uniform`` across releases. A hardcoded number would
    produce a false failure on Python 3.14 even though the behaviour (same seed ->
    same output within one interpreter) is preserved.
    """

    SCHEMA = [
        {"name": "i", "type": "int", "min": 0, "max": 1000},
        {"name": "f", "type": "float", "min": 0, "max": 100, "precision": 4},
        {"name": "e", "type": "enum", "values": ["a", "b", "c", "d", "e", "f", "g", "h"]},
        {"name": "x", "type": "expression", "expression": "{{i}} * 2"},
    ]

    def test_same_seed_gives_the_same_variables(self):
        first, first_errors = generate_variables(self.SCHEMA, SEED)
        second, second_errors = generate_variables(self.SCHEMA, SEED)
        self.assertEqual(first, second)
        self.assertEqual(first_errors, second_errors)
        self.assertEqual(list(first.keys()), list(second.keys()))

    def test_generation_is_repeatable_many_times(self):
        expected, _ = generate_variables(self.SCHEMA, SEED)
        for _ in range(5):
            again, _ = generate_variables(self.SCHEMA, SEED)
            self.assertEqual(again, expected)

    def test_generator_is_independent_of_the_global_random_module(self):
        import random as global_random

        expected, _ = generate_variables(self.SCHEMA, SEED)
        global_random.seed(999)
        global_random.random()
        actual, _ = generate_variables(self.SCHEMA, SEED)
        self.assertEqual(actual, expected)

    def test_string_and_int_seeds_are_both_accepted(self):
        # UQJ.random_seed is an int, but Random.seed also accepts str.
        first, _ = generate_variables(self.SCHEMA, "abc")
        second, _ = generate_variables(self.SCHEMA, "abc")
        self.assertEqual(first, second)

    def test_expression_stays_consistent_with_its_dependency(self):
        variables, errors = generate_variables(self.SCHEMA, SEED)
        self.assertEqual(errors, [])
        self.assertEqual(variables["x"], variables["i"] * 2)

    def test_different_seeds_produce_values_in_range(self):
        # Membership/range rather than a specific permutation, for upgrade safety.
        for seed in [1, 2, 3, 4, 5, 87654321]:
            variables, errors = generate_variables(self.SCHEMA, seed)
            self.assertEqual(errors, [])
            self.assertGreaterEqual(variables["i"], 0)
            self.assertLessEqual(variables["i"], 1000)
            self.assertIn(variables["e"], ["a", "b", "c", "d", "e", "f", "g", "h"])
