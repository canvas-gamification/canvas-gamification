from base64 import encodebytes
from io import BytesIO
from zipfile import ZipFile

import requests

from canvas_gamification.settings import JUDGE0_PASSWORD, JUDGE0_HOST
from course.utils.variables import render_text


class Grader:
    def grade(self, submission):
        raise NotImplementedError()

    def clean_up(self, submission):
        raise NotImplementedError()


class MultipleChoiceGrader(Grader):
    def grade(self, submission):
        number_of_choices = len(submission.uqj.get_rendered_choices())
        number_of_submissions = submission.uqj.submissions.exclude(pk=submission.pk).count()

        correct_answers = []
        correct_count = 0
        incorrect_count = 0
        submission_answer = submission.answer.split(",")
        submission_question_answer = submission.question.answer.split(",")

        for answer in submission_answer:
            if answer in submission_question_answer:
                if answer in correct_answers:
                    incorrect_count += 1
                else:
                    correct_answers.append(answer)
                    correct_count += 1
            else:
                incorrect_count += 1
        if correct_count - incorrect_count == len(submission_question_answer):
            return True, round(1 - number_of_submissions / (number_of_choices - 1), 2)
        elif correct_count - incorrect_count > 0:
            return True, round(
                ((correct_count - incorrect_count) / len(submission_question_answer))
                - number_of_submissions / (number_of_choices - 1),
                2,
            )
        else:
            return False, 0

    def clean_up(self, submission):
        pass


class JunitGrader(Grader):
    HEADERS = {
        "X-Auth-Token": JUDGE0_PASSWORD,
        "X-Auth-User": JUDGE0_PASSWORD,
    }
    BASE_URL = JUDGE0_HOST

    def get_compiler_script(self, submission):
        f = open("./course/grader/junit_compiler.sh", "r")
        file_names = submission.uqj.get_input_file_names() or ""
        class_names = file_names.replace(".java", ".class")

        compiler_script = f.read()
        compiler_script = compiler_script.replace("{{user_code_filename}}", file_names)
        compiler_script = compiler_script.replace("{{user_code_classname}}", class_names)
        f.close()
        return compiler_script

    def get_source_code(self, submission):
        source_code = render_text(submission.question.junit_template, submission.uqj.get_variables())
        for filename, code in submission.get_embed_files().items():
            source_code = source_code.replace("{{" + filename + "}}", code)
        return source_code

    def get_additional_file(self, submission):
        zipfile = BytesIO()
        z = ZipFile(zipfile, "w")

        # Junit jar file
        with open(
            "./course/grader/junit-platform-console-standalone-1.6.2.jar",
            "rb",
        ) as f:
            z.writestr("junit-platform-console-standalone-1.6.2.jar", f.read())

        with open("./course/grader/canvas-gamification-junit-tests.jar", "rb") as f:
            z.writestr("canvas-gamification-junit-tests.jar", f.read())

        # with open("./course/grader/spotbugs-4.7.3.tgz", "rb") as f:
        #     z.writestr("spotbugs-4.7.3.tgz", f.read())

        # Junit template file
        z.writestr("MainTest.java", self.get_source_code(submission))

        # User codes
        for filename, code in submission.get_answer_files().items():
            z.writestr(filename, code)

        # Hidden input files
        for filename, code in submission.question.get_hidden_input_files().items():
            z.writestr(
                render_text(filename, submission.uqj.get_variables()), render_text(code, submission.uqj.get_variables())
            )

        # End of writing to zipfile
        z.close()
        return encodebytes(zipfile.getvalue()).decode("UTF-8").strip()

    def grade(self, submission):
        if submission.in_progress:
            self.evaluate(submission)
        if submission.in_progress:
            return False, 0

        results = submission.get_decoded_results()
        total_testcases = len(results)
        correct_testcases = 0

        for result in results:
            if result["status"] == "PASS":
                correct_testcases += 1

        if total_testcases == 0:
            return False, 0

        return (
            correct_testcases == total_testcases,
            correct_testcases / total_testcases,
        )

    def clean_up(self, submission):
        token = submission.tokens[0]
        requests.delete(
            "{}/submissions/{}".format(self.BASE_URL, token),
            headers=self.HEADERS,
        )

    def evaluate(self, submission):
        submission.results = []

        token = submission.tokens[0]
        r = requests.get(
            "{}/submissions/{}?base64_encoded=true".format(self.BASE_URL, token),
            headers=self.HEADERS,
        )

        if r.status_code != 200:
            results = {
                "stdout": "",
                "time": "0",
                "memory": 0,
                "stderr": "",
                "token": "4e00f214-b8cb-4fcb-977b-429113c81ece",
                "compile_output": "",
                "message": "",
                "status": {
                    "id": 13,
                    "description": "Internal Error",
                },
            }
        else:
            results = r.json()
        submission.results.append(results)

    def submit(self, submission):
        submission.tokens = []

        r = requests.post(
            "{}/submissions".format(self.BASE_URL),
            data={
                "base64_encoded": False,
                "wait": False,
                "source_code": self.get_compiler_script(submission),
                "language_id": 46,
                "additional_files": self.get_additional_file(submission),
            },
            headers=self.HEADERS,
        )
        submission.tokens.append(r.json()["token"])
        self.evaluate(submission)
