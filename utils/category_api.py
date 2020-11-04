from course.models.models import Question

def count_category_questions(pk):
    questions = Question.objects.filter(pk=pk)
    # uqjs = user.question_junctions.filter(question__event=event)
    token_recv = uqjs.aggregate(total=Sum(F('tokens_received')))['total']

def get_avg_question_success: