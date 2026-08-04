"""Self-contained fixtures for the grader / XML-parsing / admin / management baseline tests.

Everything in this module is deliberately standalone: it does not import from
``test.base`` or from any other baseline test module, so the fixtures stay small
(``MyUser.save()`` and ``Question.save()`` each create a UserQuestionJunction per
user-question pair, so every extra user or question is O(n*m) rows).

It also holds the canned JUnit / SpotBugs XML documents used by the parsing tests
and the ``unittest.mock`` based Judge0 harness.  No test in this package is ever
allowed to touch the network: ``mock_judge0`` replaces the whole ``requests``
module object inside ``course.grader.grader`` so that *any* HTTP verb the grader
might reach for is a Mock.
"""

import base64
from contextlib import contextmanager

from unittest import mock

from accounts.models import MyUser
from course.models.java import JavaQuestion, JavaSubmission
from course.models.models import QuestionCategory, UserQuestionJunction

# ---------------------------------------------------------------------------
# Judge0 protocol constants (as used by course/models/models.py:CodeSubmission)
# ---------------------------------------------------------------------------

JUDGE0_IN_QUEUE = 1
JUDGE0_PROCESSING = 2
JUDGE0_ACCEPTED = 3
JUDGE0_COMPILATION_ERROR = 6
JUDGE0_INTERNAL_ERROR = 13

DEFAULT_TOKEN = "4e00f214-b8cb-4fcb-977b-429113c81ece"


def b64(text):
    """Judge0 returns base64 when ``base64_encoded=true``; mirror that here."""
    if text is None:
        return None
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def judge0_result(stdout="", stderr="", status_id=JUDGE0_ACCEPTED, description="Accepted", token=DEFAULT_TOKEN):
    """Build one element of ``CodeSubmission.results``."""
    return {
        "stdout": b64(stdout),
        "stderr": b64(stderr),
        "time": "0.5",
        "memory": 1024,
        "token": token,
        "compile_output": None,
        "message": None,
        "status": {"id": status_id, "description": description},
    }


@contextmanager
def mock_judge0(get_result=None, post_token=DEFAULT_TOKEN, get_status_code=200):
    """Patch every ``requests`` call site inside ``course.grader.grader``.

    Yields the mock stand-in for the ``requests`` module so tests can assert on
    ``.post`` / ``.get`` / ``.delete`` call args.
    """
    with mock.patch("course.grader.grader.requests") as requests_mock:
        post_response = mock.Mock(status_code=201)
        post_response.json.return_value = {"token": post_token}
        requests_mock.post.return_value = post_response

        get_response = mock.Mock(status_code=get_status_code)
        get_response.json.return_value = judge0_result() if get_result is None else get_result
        requests_mock.get.return_value = get_response

        requests_mock.delete.return_value = mock.Mock(status_code=204)

        yield requests_mock


# ---------------------------------------------------------------------------
# Canned JUnit XML (shape copied from test/junit/output/TEST-junit-jupiter.xml,
# trimmed to the parts parse_junit_xml actually looks at)
# ---------------------------------------------------------------------------

JUNIT_ALL_PASS = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="JUnit Jupiter" tests="2" skipped="0" failures="0" errors="0" time="0.045">
<testcase name="testAddition()" classname="MainTest" time="0.01"/>
<testcase name="testSubtractionOfNumbers()" classname="MainTest" time="0.02"/>
</testsuite>
"""

JUNIT_SOME_FAIL = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="JUnit Jupiter" tests="4" skipped="0" failures="1" errors="1" time="0.045">
<testcase name="testAddition()" classname="MainTest" time="0.01"/>
<testcase name="testSubtractionOfNumbers()" classname="MainTest" time="0.02">
<failure message="expected: &lt;5&gt; but was: &lt;4&gt; ==&gt; arrays first differed" type="org.opentest4j.AssertionFailedError">stack trace here</failure>
</testcase>
<testcase name="testDivision[1]" classname="MainTest" time="0.03">
<error message="java.lang.ArithmeticException: / by zero" type="java.lang.ArithmeticException">trace</error>
</testcase>
<testcase name="testMultiplication()" classname="MainTest" time="0.04"/>
</testsuite>
"""

JUNIT_ZERO_TESTS = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="JUnit Jupiter" tests="0" skipped="0" failures="0" errors="0" time="0.001">
</testsuite>
"""

# Same test name reported three times: PASS, FAIL, PASS.  parse_junit_xml keeps
# the FAIL (dedupe-preferring-FAIL).
JUNIT_DUPLICATE_NAMES = """<testsuite>
<testcase name="testSame()" classname="MainTest"/>
<testcase name="testSame()" classname="MainTest"><failure message="boom">t</failure></testcase>
<testcase name="testSame()" classname="MainTest"/>
</testsuite>
"""

# FAIL first, PASS afterwards -- the later PASS must not overwrite the FAIL.
JUNIT_DUPLICATE_FAIL_FIRST = """<testsuite>
<testcase name="testSame()" classname="MainTest"><failure message="boom">t</failure></testcase>
<testcase name="testSame()" classname="MainTest"/>
</testsuite>
"""

# A <failure>/<error> element without a message attribute.
JUNIT_FAILURE_NO_MESSAGE = """<testsuite>
<testcase name="testNoMessage()"><failure type="org.opentest4j.AssertionFailedError">t</failure></testcase>
</testsuite>
"""

JUNIT_ERROR_NO_MESSAGE = """<testsuite>
<testcase name="testNoMessage()"><error type="java.lang.Exception">t</error></testcase>
</testsuite>
"""

# A <testcase> without the required name attribute.
JUNIT_MISSING_NAME = """<testsuite>
<testcase name="testFirst()"/>
<testcase classname="MainTest"/>
<testcase name="testThird()"/>
</testsuite>
"""

# Both <error> and <failure> on the same testcase: <failure> is evaluated last
# so its message wins.
JUNIT_ERROR_AND_FAILURE = """<testsuite>
<testcase name="testBoth()">
<error message="error message">t</error>
<failure message="failure message">t</failure>
</testcase>
</testsuite>
"""

# ---------------------------------------------------------------------------
# Canned SpotBugs XML
# ---------------------------------------------------------------------------

SPOTBUGS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<BugCollection version="4.7.3">
<BugInstance type="DLS_DEAD_LOCAL_STORE" priority="2" rank="18" abbrev="DLS" category="STYLE">
<ShortMessage>Dead store to local variable</ShortMessage>
<LongMessage>Dead store to x in Main.main(String[])</LongMessage>
<Class classname="Main">
<SourceLine classname="Main" start="1" end="9" sourcefile="Main.java">
<Message>At Main.java:[lines 1-9]</Message>
</SourceLine>
<Message>In class Main</Message>
</Class>
<SourceLine classname="Main" start="4" end="4" sourcefile="Main.java">
<Message>At Main.java:[line 4]</Message>
</SourceLine>
</BugInstance>
<BugInstance type="UC_USELESS_VOID_METHOD" priority="1" rank="20" abbrev="UC" category="PERFORMANCE">
<ShortMessage>Useless non-empty void method</ShortMessage>
<LongMessage>Method Main.helper() seems to be useless</LongMessage>
<SourceLine classname="Main" start="11" end="12" sourcefile="Main.java">
<Message>At Main.java:[lines 11-12]</Message>
</SourceLine>
</BugInstance>
<BugPattern type="DLS_DEAD_LOCAL_STORE" abbrev="DLS" category="STYLE">
<ShortDescription>Dead store to local variable</ShortDescription>
<Details>&lt;p&gt; This instruction assigns a value that is never used.&lt;/p&gt;</Details>
</BugPattern>
<BugPattern type="UC_USELESS_VOID_METHOD" abbrev="UC" category="PERFORMANCE">
<ShortDescription>Useless non-empty void method</ShortDescription>
<Details>&lt;p&gt; This void method does not do anything useful.&lt;/p&gt;</Details>
</BugPattern>
</BugCollection>
"""

# BugInstance whose <type> attribute is missing.
SPOTBUGS_MISSING_TYPE = """<BugCollection>
<BugInstance priority="2">
<ShortMessage>a</ShortMessage>
<LongMessage>b</LongMessage>
<SourceLine><Message>m</Message></SourceLine>
</BugInstance>
</BugCollection>
"""

# BugInstance with no <SourceLine> child at all.
SPOTBUGS_MISSING_SOURCELINE = """<BugCollection>
<BugInstance type="T">
<ShortMessage>a</ShortMessage>
<LongMessage>b</LongMessage>
</BugInstance>
</BugCollection>
"""


# ---------------------------------------------------------------------------
# Model fixtures -- keep these tiny, every question/user pair costs a UQJ row.
# ---------------------------------------------------------------------------


def create_user(username="grader_user", role="Student"):
    user = MyUser.objects.create_user(username, "{}@example.com".format(username), "aaaaaaaa")
    if role != user.role:
        user.role = role
        user.save()
    return user


def create_superuser(username="grader_admin", password="aaaaaaaa"):
    return MyUser.objects.create_superuser(username, "{}@example.com".format(username), password)


def create_category(name="Grader Category"):
    category = QuestionCategory(name=name, description=name)
    category.save()
    return category


def create_java_question(author=None, category=None, title="Sum of two numbers", event=None):
    """One JavaQuestion with a single compiled input file."""
    question = JavaQuestion(
        title=title,
        text="Write a program that adds two numbers",
        answer="",
        max_submission_allowed=5,
        tutorial=None,
        author=author,
        category=category,
        difficulty="EASY",
        is_verified=True,
        variables=[],
        variation_types=[],
        junit_template="class MainTest { {{Main.java}} }",
        input_files=[
            {
                "name": "Main.java",
                "compile": True,
                "template": "public class Main {}",
                "hidden": False,
            }
        ],
        event=event,
    )
    question.save()
    return question


def get_uqj(user, question):
    """``Question.save()``/``MyUser.save()`` already created the junction."""
    return UserQuestionJunction.objects.get(user=user, question=question)


def build_java_submission(uqj, results, answer_files=None, tokens=None):
    """An *unsaved* JavaSubmission -- saving would trigger grading + clean_up."""
    return JavaSubmission(
        uqj=uqj,
        answer_files={"Main.java": "public class Main {}"} if answer_files is None else answer_files,
        tokens=[DEFAULT_TOKEN] if tokens is None else tokens,
        results=results,
    )
