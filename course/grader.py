class Grader:
    def grade(self, submission):
        raise NotImplementedError()


class MultipleChoiceGrader(Grader):

    def __init__(self, question, user):
        self.question = question
        self.user = user

    def grade(self, submission):
        if submission.answer != self.question.answer:
            return False, 0
        else:
            number_of_choices = len(self.question.choices.items())
            number_of_submissions = self.user.submissions.filter(question=self.question).exclude(pk=submission.pk).count()

            return True, 1 - number_of_submissions/(number_of_choices - 1)
