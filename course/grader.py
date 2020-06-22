import requests


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
                "https://judge0.p.rapidapi.com/submissions/{}?base64_encoded=false".format(token),
                headers={
                    'X-RapidAPI-Host': 'judge0.p.rapidapi.com',
                    'X-RapidAPI-Key': 'e29a947330msh9b3e32544b404bfp146d9djsn63c86eaa6d11',
                }
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
                "https://judge0.p.rapidapi.com/submissions/",
                data={
                    "base64_encoded": False,
                    "wait": False,
                    "source_code": submission.code,
                    "language_id": 62,
                    "stdin": test_case['input'],
                    "expected_output": test_case['output'],
                },
                headers={
                    'X-RapidAPI-Host': 'judge0.p.rapidapi.com',
                    'X-RapidAPI-Key': 'e29a947330msh9b3e32544b404bfp146d9djsn63c86eaa6d11',
                },
            )
            submission.tokens.append(r.json()['token'])
        self.evaluate(submission)


class ParsonsGrader(Grader):

    def grade(self, submission):
        return 0
