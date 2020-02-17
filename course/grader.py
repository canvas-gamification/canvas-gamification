class Grader:
    def grade(self, solution):
        raise NotImplementedError()


class MultipleChoiceGrader(Grader):

    def __init__(self, answer):
        self.answer = answer

    def grade(self, solution):
        return 1.0 if solution == self.answer else 0.0
