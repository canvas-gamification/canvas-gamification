import requests

from canvas_gamification.settings import JUDGE0_PASSWORD, JUDGE0_HOST


class Grader:

    def __init__(self, question, user):
        self.question = question
        self.user = user

    def grade(self, submission):
        raise NotImplementedError()


class MultipleChoiceGrader(Grader):

    def grade(self, submission):
        if submission.answer != self.question.answer:
            return False, 0
        else:
            number_of_choices = len(self.question.choices.items())
            number_of_submissions = self.user.submissions.filter(question=self.question).exclude(
                pk=submission.pk).count()

            return True, 1 - number_of_submissions / (number_of_choices - 1)


class JavaGrader(Grader):
    HEADERS = {
        'X-Auth-Token': JUDGE0_PASSWORD,
    }
    BASE_URL = JUDGE0_HOST

    def grade(self, submission):
        if submission.in_progress:
            self.evaluate(submission)
        if submission.in_progress:
            return False, 0

        total_test_cases = len(self.question.test_cases)
        correct_test_cases = 0

        for i, result in enumerate(submission.results):
            if result['status']['id'] == 3:
                correct_test_cases += 1

        return correct_test_cases == total_test_cases, correct_test_cases / total_test_cases

    def evaluate(self, submission):
        submission.results = []

        for i, test_case in enumerate(self.question.test_cases):
            token = submission.tokens[i]
            r = requests.get(
                "{}/submissions/{}?base64_encoded=false".format(self.BASE_URL, token),
                headers=self.HEADERS,
            )
            submission.results.append(r.json())
        if not submission.in_progress:
            submission.calculate_grade()
        else:
            submission.save()

    def submit(self, submission):
        submission.tokens = []

        for test_case in self.question.test_cases:
            r = requests.post(
                "{}/submissions".format(self.BASE_URL),
                data={
                    "base64_encoded": False,
                    "wait": False,
                    "source_code": submission.code,
                    "language_id": 4,
                    "stdin": test_case['input'],
                    "expected_output": test_case['output'],
                },
                headers=self.HEADERS,
            )
            submission.tokens.append(r.json()['token'])
        self.evaluate(submission)


class ParsonsGrader(Grader):
    HEADERS = {
        'X-Auth-Token': JUDGE0_PASSWORD,
    }
    BASE_URL = JUDGE0_HOST

    def get_source_code(self, submission):
        return self.question.junit_template.replace("{{code}}", submission.code)

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

        if not submission.in_progress:
            submission.calculate_grade()
        else:
            submission.save()

    def submit(self, submission):
        submission.tokens = []

        r = requests.post(
            "{}/submissions".format(self.BASE_URL),
            data={
                "base64_encoded": False,
                "wait": False,
                "source_code": self.get_source_code(submission),
                "language_id": 5,
            },
            headers=self.HEADERS,
        )
        submission.tokens.append(r.json()['token'])
        self.evaluate(submission)