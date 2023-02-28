import re

from django.template.loader import render_to_string


def brackets_bugs(file_name, code):
    lines = code.split("\n")
    stack = []
    matching = {
        "]": "[",
        "}": "{",
        ")": "(",
    }
    for i, line in enumerate(lines):
        for c in line:
            if c in "[{(":
                stack.append(c)
            if c in "]})":
                if len(stack) == 0 or stack.pop() != matching[c]:
                    return [
                        {
                            "type": "BRACKETS",
                            "short_message": "Mismatching brackets",
                            "long_message": "",
                            "source_line": "At {} [line {}]".format(file_name, i + 1),
                        }
                    ]
    if len(stack) != 0:
        return [
            {
                "type": "BRACKETS",
                "short_message": "Mismatching brackets",
                "long_message": "",
                "source_line": "At {} [line {}]".format(file_name, len(lines)),
            }
        ]
    return []


def find_bugs_with_regex(file_name, code, regex, bug_type, short_message):
    r = re.compile(regex, re.MULTILINE)
    bugs = []
    for m in r.finditer(code):
        line = code[: m.start()].count("\n") + 1
        bugs.append(
            {
                "type": bug_type,
                "short_message": short_message,
                "long_message": str(m.group()),
                "source_line": "At {} [line {}]".format(file_name, line),
            }
        )
    return bugs


def find_custom_bugs(file_name, code):
    return (
        brackets_bugs(file_name, code)
        + find_bugs_with_regex(
            file_name,
            code,
            r"for\s*\([^()]*,[^()]*\)",
            "FOR_LOOP_INCORRECT_SEPARATORS",
            "Incorrect separators in a for loop",
        )
        + find_bugs_with_regex(
            file_name,
            code,
            r"(for|while|if)\s*({|\[)",
            "LOOP_INCORRECT_BRACKETS",
            "Incorrect brackets",
        )
        + find_bugs_with_regex(
            file_name,
            code,
            r"if\s*\([^{}]*[^=]=[^=][^{}]*\)\s*{",
            "IF_ASSIGNMENT",
            "Assignment in if statement",
        )
        + find_bugs_with_regex(
            file_name,
            code,
            r"^.*(=<|=>).*$",
            "INEQ",
            "Incorrect inequality operator =< or =>",
        )
        + find_bugs_with_regex(
            file_name,
            code,
            r"(if|for|while)\s*\([^{}]*\)\s*;",
            "SEMICOLON_AFTER_FLOW",
            "Useless flow controll",
        )
    )


def find_bugs_from_compile_error(file_name, error):
    bugs = []
    if error.find("error: incompatible types") > -1:
        bugs.append(
            {
                "type": "INCOMPATIBLE_TYPES",
                "short_message": "Compilation Error: Incompatible types",
                "long_message": "",
                "source_line": "At {}".format(file_name),
            }
        )
    if error.find("error: missing return statement") > -1:
        bugs.append(
            {
                "type": "MISSING_RETURN",
                "short_message": "Compilation Error: Missing return statement",
                "long_message": "",
                "source_line": "At {}".format(file_name),
            }
        )
    if error.find("error: missing method body, or declare abstract") > -1:
        bugs.append(
            {
                "type": "SEMICOLON_END_METHOD",
                "short_message": "Compilation Error: Incorrect semicolon at the end of a method header",
                "long_message": "",
                "source_line": "At {}".format(file_name),
            }
        )
    if error.find("error: not a statement") > -1:
        bugs.append(
            {
                "type": "NOT_A_STATEMENT",
                "short_message": "Compilation Error: Not a statement",
                "long_message": "",
                "source_line": "At {}".format(file_name),
            }
        )
    return bugs


def custom_patterns():
    return [
        {"type": "INEQ", "short_description": "", "details": render_to_string("bug_details/INEQ.html")},
        {"type": "BRACKETS", "short_description": "", "details": render_to_string("bug_details/BRACKETS.html")},
        {
            "type": "FOR_LOOP_INCORRECT_SEPARATORS",
            "short_description": "",
            "details": render_to_string("bug_details/FOR_LOOP_INCORRECT_SEPARATORS.html"),
        },
        {
            "type": "LOOP_INCORRECT_BRACKETS",
            "short_description": "",
            "details": render_to_string("bug_details/LOOP_INCORRECT_BRACKETS.html"),
        },
        {
            "type": "SEMICOLON_AFTER_FLOW",
            "short_description": "",
            "details": render_to_string("bug_details/SEMICOLON_AFTER_FLOW.html"),
        },
        {
            "type": "INCOMPATIBLE_TYPES",
            "short_description": "",
            "details": render_to_string("bug_details/INCOMPATIBLE_TYPES.html"),
        },
        {
            "type": "MISSING_RETURN",
            "short_description": "",
            "details": render_to_string("bug_details/MISSING_RETURN.html"),
        },
        {
            "type": "SEMICOLON_END_METHOD",
            "short_description": "",
            "details": render_to_string("bug_details/SEMICOLON_END_METHOD.html"),
        },
        {
            "type": "NOT_A_STATEMENT",
            "short_description": "",
            "details": render_to_string("bug_details/NOT_A_STATEMENT.html"),
        },
    ]
