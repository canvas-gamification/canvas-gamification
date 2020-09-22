from base64 import encodebytes
from io import BytesIO
from zipfile import ZipFile

import requests

from canvas_gamification.settings import JUDGE0_PASSWORD, JUDGE0_HOST
from course.utils.variables import render_text


class Grader:

    def grade(self, submission):
        raise NotImplementedError()


class MultipleChoiceGrader(Grader):

    def grade(self, submission):
        if submission.answer != submission.question.answer:
            return False, 0
        else:
            number_of_choices = len(submission.uqj.get_rendered_choices())

            number_of_submissions = submission.uqj.submissions.exclude(pk=submission.pk).count()

            return True, 1 - number_of_submissions / (number_of_choices - 1)


class JunitGrader(Grader):
    HEADERS = {
        'X-Auth-Token': JUDGE0_PASSWORD,
    }
    BASE_URL = JUDGE0_HOST

    def get_source_code(self, submission):
        code = render_text(submission.question.junit_template, submission.uqj.get_variables())
        return code.replace("{{code}}", submission.answer)

    def get_additional_file(self, submission):
        code = render_text(submission.answer, submission.uqj.get_variables())
        filename = submission.question.additional_file_name

        if not filename:
            return None

        zipfile = BytesIO()
        z = ZipFile(zipfile, "w")
        z.writestr(filename, code)
        z.close()

        return encodebytes(zipfile.getvalue()).decode("UTF-8").strip()

    def grade(self, submission):
        if submission.in_progress:
            self.evaluate(submission)
        if submission.in_progress:
            return False, 0

        return (True, 1) if submission.results[0]['status']['id'] == 3 else (False, 0)

    def evaluate(self, submission):
        submission.results = []

        token = submission.tokens[0]
        r = requests.get(
            "{}/submissions/{}?base64_encoded=true".format(self.BASE_URL, token),
            headers=self.HEADERS,
        )
        submission.results.append(r.json())

    def submit(self, submission):
        submission.tokens = []

        r = requests.post(
            "{}/submissions".format(self.BASE_URL),
            data={
                "base64_encoded": False,
                "wait": False,
                "source_code": self.get_source_code(submission),
                "language_id": 5,
                "additional_files": self.get_additional_file(submission),
                "compiler_options": submission.question.additional_file_name,
            },
            headers=self.HEADERS,
        )
        submission.tokens.append(r.json()['token'])
        self.evaluate(submission)
