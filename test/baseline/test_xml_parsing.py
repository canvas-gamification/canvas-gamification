"""Baseline tests for the BeautifulSoup-backed XML helpers.

``course/utils/junit_xml.py`` and ``course/utils/spotbugs_xml.py`` both parse with
``BeautifulSoup(xml, "html.parser")``.  bs4 is being upgraded 4.9 -> 4.15, so these
tests pin element ordering, missing-attribute handling and empty documents.

Assertions are on parsed *values* only -- never on BeautifulSoup's own exception
text (both parsers swallow exceptions and log them).
"""

from django.test import TestCase

from course.utils.custom_bugs import (
    brackets_bugs,
    find_bugs_from_compile_error,
    find_bugs_with_regex,
    find_custom_bugs,
)
from course.utils.junit_xml import (
    convert_camel_case_to_title_case,
    format_message,
    format_test_name,
    parse_junit_xml,
)
from course.utils.spotbugs_xml import parse_spotbugs_xml
from test.baseline.fixtures_grader import (
    JUNIT_ALL_PASS,
    JUNIT_DUPLICATE_FAIL_FIRST,
    JUNIT_DUPLICATE_NAMES,
    JUNIT_ERROR_AND_FAILURE,
    JUNIT_ERROR_NO_MESSAGE,
    JUNIT_FAILURE_NO_MESSAGE,
    JUNIT_MISSING_NAME,
    JUNIT_SOME_FAIL,
    JUNIT_ZERO_TESTS,
    SPOTBUGS_MISSING_SOURCELINE,
    SPOTBUGS_MISSING_TYPE,
    SPOTBUGS_XML,
    build_java_submission,
    create_category,
    create_java_question,
    create_user,
    get_uqj,
    judge0_result,
)


def parsed(xml):
    """parse_junit_xml returns a dict_values view, not a list."""
    return list(parse_junit_xml(xml))


class ParseJunitXmlTests(TestCase):
    def test_all_pass_preserves_document_order(self):
        results = parsed(JUNIT_ALL_PASS)
        self.assertEqual(
            [(r["name"], r["status"], r["message"]) for r in results],
            [
                ("Test addition", "PASS", ""),
                ("Test subtraction of numbers", "PASS", ""),
            ],
        )

    def test_failures_and_errors(self):
        results = parsed(JUNIT_SOME_FAIL)
        self.assertEqual(
            [(r["name"], r["status"]) for r in results],
            [
                ("Test addition", "PASS"),
                ("Test subtraction of numbers", "FAIL"),
                ("Test division", "FAIL"),
                ("Test multiplication", "PASS"),
            ],
        )
        by_name = {r["name"]: r for r in results}
        self.assertEqual(by_name["Test subtraction of numbers"]["message"], "expected: <5> but was: <4> ")
        self.assertEqual(by_name["Test division"]["message"], "java.lang.ArithmeticException: / by zero")

    def test_zero_tests(self):
        self.assertEqual(parsed(JUNIT_ZERO_TESTS), [])

    def test_empty_and_garbage_documents(self):
        self.assertEqual(parsed(""), [])
        self.assertEqual(parsed("   "), [])
        self.assertEqual(parsed("this is not xml at all"), [])
        self.assertEqual(parsed("<testsuite></testsuite>"), [])
        self.assertEqual(parsed("<html><body><p>oops</p></body></html>"), [])

    def test_duplicate_names_prefer_fail(self):
        """PASS, FAIL, PASS for the same test name collapses to a single FAIL."""
        results = parsed(JUNIT_DUPLICATE_NAMES)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "FAIL")
        self.assertEqual(results[0]["message"], "boom")

    def test_duplicate_names_fail_first_is_not_overwritten_by_a_later_pass(self):
        results = parsed(JUNIT_DUPLICATE_FAIL_FIRST)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "FAIL")

    def test_failure_without_message_attribute(self):
        results = parsed(JUNIT_FAILURE_NO_MESSAGE)
        self.assertEqual(results, [{"name": "Test no message", "status": "FAIL", "message": "Unexpected error"}])

    def test_error_without_message_attribute(self):
        results = parsed(JUNIT_ERROR_NO_MESSAGE)
        self.assertEqual(results, [{"name": "Test no message", "status": "FAIL", "message": "Unexpected error"}])

    def test_error_and_failure_on_the_same_testcase_failure_wins(self):
        results = parsed(JUNIT_ERROR_AND_FAILURE)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "FAIL")
        self.assertEqual(results[0]["message"], "failure message")

    def test_testcase_without_name_attribute_aborts_the_whole_parse(self):
        # KNOWN-BUG: course/utils/junit_xml.py:15 does `test_case["name"]`, which
        # raises KeyError for a <testcase> with no name attribute.  The bare
        # `except Exception` at :33 swallows it, so parsing stops at the bad
        # element and the caller silently gets a truncated result set -- here only
        # the first of three testcases.  JunitGrader.grade would then report 1/1.
        results = parsed(JUNIT_MISSING_NAME)
        self.assertEqual([r["name"] for r in results], ["Test first"])


class JunitNameFormattingTests(TestCase):
    def test_convert_camel_case_to_title_case(self):
        self.assertEqual(convert_camel_case_to_title_case("testAddition"), "test Addition")
        self.assertEqual(convert_camel_case_to_title_case("HTMLParser"), "HTML Parser")
        self.assertEqual(convert_camel_case_to_title_case("a"), "a")
        self.assertEqual(convert_camel_case_to_title_case(""), "")

    def test_format_test_name(self):
        self.assertEqual(format_test_name("testAddition()"), "Test addition")
        self.assertEqual(format_test_name("testSubtractionOfNumbers()"), "Test subtraction of numbers")
        # a single-digit JUnit parameterised-test index suffix is stripped
        self.assertEqual(format_test_name("testDivision[1]"), "Test division")
        # KNOWN-BUG: convert_camel_case_to_title_case (junit_xml.py:47) splits
        # digit-digit pairs, so a multi-digit repetition index becomes "[1 2]"
        # and the `\[\d+\]$` strip at :53 no longer matches.  Repetitions 10+ of
        # a parameterised test therefore show up as separate test names.
        self.assertEqual(format_test_name("testDivision[12]"), "Test division[1 2]")
        # the index is only stripped when it is at the very end
        self.assertEqual(format_test_name("test[1]Division"), "Test[1] division")
        self.assertEqual(format_test_name(""), "")

    def test_format_message(self):
        self.assertEqual(format_message("plain message"), "plain message")
        self.assertEqual(format_message("expected: <1> but was: <2> ==> detail"), "expected: <1> but was: <2> ")
        self.assertEqual(format_message("==> leading"), "")
        self.assertEqual(format_message(""), "")


class ParseSpotbugsXmlTests(TestCase):
    def test_full_document(self):
        result = parse_spotbugs_xml(SPOTBUGS_XML)
        self.assertEqual([b["type"] for b in result["bugs"]], ["DLS_DEAD_LOCAL_STORE", "UC_USELESS_VOID_METHOD"])
        self.assertEqual(result["bugs"][0]["short_message"], "Dead store to local variable")
        self.assertEqual(result["bugs"][0]["long_message"], "Dead store to x in Main.main(String[])")
        self.assertEqual(result["bugs"][1]["source_line"], "At Main.java:[lines 11-12]")

    def test_source_line_prefers_the_direct_child_over_a_nested_one(self):
        # <BugInstance> has a <Class><SourceLine> as well as its own <SourceLine>;
        # `find("sourceline", recursive=False)` must pick the direct child.
        result = parse_spotbugs_xml(SPOTBUGS_XML)
        self.assertEqual(result["bugs"][0]["source_line"], "At Main.java:[line 4]")

    def test_patterns(self):
        result = parse_spotbugs_xml(SPOTBUGS_XML)
        self.assertEqual([p["type"] for p in result["patterns"]], ["DLS_DEAD_LOCAL_STORE", "UC_USELESS_VOID_METHOD"])
        self.assertEqual(result["patterns"][0]["short_description"], "Dead store to local variable")
        # entity-encoded HTML inside <Details> is decoded by the parser
        self.assertEqual(
            result["patterns"][0]["details"],
            "<p> This instruction assigns a value that is never used.</p>",
        )

    def test_empty_and_garbage_documents(self):
        empty = {"bugs": [], "patterns": []}
        self.assertEqual(parse_spotbugs_xml(""), empty)
        self.assertEqual(parse_spotbugs_xml("   "), empty)
        self.assertEqual(parse_spotbugs_xml("<BugCollection></BugCollection>"), empty)
        self.assertEqual(parse_spotbugs_xml("not xml"), empty)

    def test_bug_instance_without_type_attribute_aborts_the_parse(self):
        # KNOWN-BUG: course/utils/spotbugs_xml.py:17 does `bug_instance["type"]`;
        # a missing attribute raises KeyError, which the bare `except Exception`
        # at :34 swallows, so both bugs *and* patterns come back empty.
        self.assertEqual(parse_spotbugs_xml(SPOTBUGS_MISSING_TYPE), {"bugs": [], "patterns": []})

    def test_bug_instance_without_source_line_aborts_the_parse(self):
        # KNOWN-BUG: same swallow -- `find("sourceline", recursive=False)` returns
        # None and `.message` raises AttributeError, silently yielding no bugs.
        self.assertEqual(parse_spotbugs_xml(SPOTBUGS_MISSING_SOURCELINE), {"bugs": [], "patterns": []})


class BracketsBugsTests(TestCase):
    def test_balanced_code_has_no_bugs(self):
        self.assertEqual(brackets_bugs("A.java", "public class A {\n  int x = f(1);\n}\n"), [])
        self.assertEqual(brackets_bugs("A.java", ""), [])

    def test_unexpected_closing_bracket_reports_its_line(self):
        bugs = brackets_bugs("A.java", "class A {\n}\n}\n")
        self.assertEqual(len(bugs), 1)
        self.assertEqual(bugs[0]["type"], "BRACKETS")
        self.assertEqual(bugs[0]["short_message"], "Mismatching brackets")
        self.assertEqual(bugs[0]["long_message"], "")
        self.assertEqual(bugs[0]["source_line"], "At A.java [line 3]")

    def test_mismatched_bracket_kind(self):
        bugs = brackets_bugs("A.java", "int[] a = new int[3);\n")
        self.assertEqual(len(bugs), 1)
        self.assertEqual(bugs[0]["source_line"], "At A.java [line 1]")

    def test_unclosed_bracket_reports_the_last_line(self):
        bugs = brackets_bugs("A.java", "class A {\n  void f() {\n")
        self.assertEqual(len(bugs), 1)
        # the trailing newline makes split("\n") produce 3 elements
        self.assertEqual(bugs[0]["source_line"], "At A.java [line 3]")

    def test_only_the_first_mismatch_is_reported(self):
        self.assertEqual(len(brackets_bugs("A.java", "}\n}\n}\n")), 1)


class FindCustomBugsTests(TestCase):
    """One test per regex in course/utils/custom_bugs.py:find_custom_bugs."""

    def assert_single(self, bugs, bug_type, long_message, line):
        self.assertEqual([b["type"] for b in bugs], [bug_type])
        self.assertEqual(bugs[0]["long_message"], long_message)
        self.assertEqual(bugs[0]["source_line"], "At A.java [line {}]".format(line))

    def test_clean_code_has_no_bugs(self):
        self.assertEqual(find_custom_bugs("A.java", "public class A {\n  int x = f(1);\n}\n"), [])

    def test_for_loop_incorrect_separators(self):
        bugs = find_custom_bugs("A.java", "for (int i = 0, i < 10, i++) {\n}\n")
        self.assert_single(bugs, "FOR_LOOP_INCORRECT_SEPARATORS", "for (int i = 0, i < 10, i++)", 1)

    def test_loop_incorrect_brackets(self):
        bugs = find_custom_bugs("A.java", "if {x > 1} {\n}\n")
        self.assert_single(bugs, "LOOP_INCORRECT_BRACKETS", "if {", 1)

    def test_loop_incorrect_brackets_matches_while_and_for(self):
        for keyword in ["for", "while", "if"]:
            bugs = find_bugs_with_regex(
                "A.java", keyword + " [x]", r"(for|while|if)\s*({|\[)", "LOOP_INCORRECT_BRACKETS", "Incorrect brackets"
            )
            self.assertEqual([b["type"] for b in bugs], ["LOOP_INCORRECT_BRACKETS"])

    def test_if_assignment(self):
        bugs = find_custom_bugs("A.java", "if (x = 5) {\n}\n")
        self.assert_single(bugs, "IF_ASSIGNMENT", "if (x = 5) {", 1)

    def test_if_equality_is_not_flagged(self):
        self.assertEqual(find_custom_bugs("A.java", "if (x == 5) {\n}\n"), [])

    def test_incorrect_inequality_operator(self):
        bugs = find_custom_bugs("A.java", "int a = 1;\nboolean b = a =< 5;\n")
        self.assert_single(bugs, "INEQ", "boolean b = a =< 5;", 2)

    def test_incorrect_inequality_operator_greater(self):
        bugs = find_custom_bugs("A.java", "boolean b = a => 5;\n")
        self.assert_single(bugs, "INEQ", "boolean b = a => 5;", 1)

    def test_inequality_inside_an_if_also_matches_the_if_assignment_regex(self):
        # Documented quirk: "=<" satisfies the IF_ASSIGNMENT pattern too, so a
        # single typo produces two bugs, IF_ASSIGNMENT before INEQ.
        bugs = find_custom_bugs("A.java", "int a;\nif (a =< 5) { }\n")
        self.assertEqual([b["type"] for b in bugs], ["IF_ASSIGNMENT", "INEQ"])

    def test_semicolon_after_flow(self):
        bugs = find_custom_bugs("A.java", "for (int i = 0; i < 3; i++);\n")
        self.assert_single(bugs, "SEMICOLON_AFTER_FLOW", "for (int i = 0; i < 3; i++);", 1)

    def test_brackets_bug_is_reported_first(self):
        bugs = find_custom_bugs("A.java", "if (x = 5) {\n")
        self.assertEqual([b["type"] for b in bugs], ["BRACKETS", "IF_ASSIGNMENT"])

    def test_line_numbers_count_preceding_newlines(self):
        code = "\n\n\nfor (int i = 0, i < 10, i++) {}\n"
        bugs = find_custom_bugs("A.java", code)
        self.assertEqual(bugs[0]["source_line"], "At A.java [line 4]")


class FindBugsFromCompileErrorTests(TestCase):
    def test_no_error_text(self):
        self.assertEqual(find_bugs_from_compile_error("A.java", ""), [])
        self.assertEqual(find_bugs_from_compile_error("A.java", "some unrelated warning"), [])

    def test_each_recognised_compile_error(self):
        cases = [
            ("A.java:3: error: incompatible types", "INCOMPATIBLE_TYPES"),
            ("A.java:3: error: missing return statement", "MISSING_RETURN"),
            ("A.java:3: error: missing method body, or declare abstract", "SEMICOLON_END_METHOD"),
            ("A.java:3: error: not a statement", "NOT_A_STATEMENT"),
        ]
        for text, bug_type in cases:
            bugs = find_bugs_from_compile_error("A.java", text)
            self.assertEqual([b["type"] for b in bugs], [bug_type])
            self.assertEqual(bugs[0]["source_line"], "At A.java")

    def test_all_errors_together_keep_a_fixed_order(self):
        text = (
            "error: incompatible types\n"
            "error: missing return statement\n"
            "error: missing method body, or declare abstract\n"
            "error: not a statement\n"
        )
        self.assertEqual(
            [b["type"] for b in find_bugs_from_compile_error("A.java", text)],
            ["INCOMPATIBLE_TYPES", "MISSING_RETURN", "SEMICOLON_END_METHOD", "NOT_A_STATEMENT"],
        )


class CodeSubmissionBugsTests(TestCase):
    """``CodeSubmission.bugs`` glues both parsers together with the custom rules."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_user("xml_user")
        cls.category = create_category("XML Category")
        cls.question = create_java_question(author=cls.user, category=cls.category)

    def setUp(self):
        self.uqj = get_uqj(self.user, self.question)

    def test_bugs_combines_spotbugs_custom_and_compile_error_bugs(self):
        stdout = JUNIT_ALL_PASS + "==SEPARATOR==" + SPOTBUGS_XML
        submission = build_java_submission(
            self.uqj,
            [judge0_result(stdout=stdout, stderr="A.java:1: error: not a statement")],
            answer_files={"Main.java": "if (x = 5) {\n}\n"},
        )
        bugs = submission.bugs
        types = [b["type"] for b in bugs["bugs"]]
        self.assertEqual(types, ["DLS_DEAD_LOCAL_STORE", "UC_USELESS_VOID_METHOD", "IF_ASSIGNMENT", "NOT_A_STATEMENT"])
        # custom_patterns() are always appended to whatever SpotBugs reported
        pattern_types = [p["type"] for p in bugs["patterns"]]
        self.assertEqual(pattern_types[:2], ["DLS_DEAD_LOCAL_STORE", "UC_USELESS_VOID_METHOD"])
        self.assertIn("BRACKETS", pattern_types)
        self.assertIn("NOT_A_STATEMENT", pattern_types)
        # KNOWN-BUG: find_custom_bugs can emit an "IF_ASSIGNMENT" bug but
        # custom_patterns() (course/utils/custom_bugs.py:138-177) has no entry for
        # it, so the UI has no details/description to show for that bug type.
        self.assertNotIn("IF_ASSIGNMENT", pattern_types)

    def test_bugs_without_a_separator_yields_only_custom_bugs(self):
        submission = build_java_submission(
            self.uqj,
            [judge0_result(stdout=JUNIT_ALL_PASS)],
            answer_files={"Main.java": "public class Main {}"},
        )
        bugs = submission.bugs
        self.assertEqual(bugs["bugs"], [])
        self.assertEqual(len(bugs["patterns"]), 9)
