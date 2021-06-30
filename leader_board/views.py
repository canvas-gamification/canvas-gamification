from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import LeaderBoardAssignedStudents, Leader_Board
from canvas.models import CanvasCourseRegistration


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

@csrf_exempt
def leader_board_view(request, pk):
    leaders_boards = LeaderBoard.objects.all().values    
    leaders_boards = [x for x in leaders_boards.iterator()]
    return JsonResponse(data={'data': leaders_boards}, safe=False)

@csrf_exempt
def get_all_students_leader_board(request):
    leader_board_id = request.Get.get('leader_board_id')
    leader_board = LeaderBoard.onjects.get(id=int(leader_board_id))
    leader_board_students = LeaderBoardAssignedStudents.objects.filter(leader_board=leader_board)

    students_list =[]
    for obj in leader_board_students:
        student =obj.student
        course_detail = CanvasCourseRegistration.objects.filter(user=student, course = leader_board.assigned_course).last()
        if course_detail:
            tokens_info = course_detail.available_tokens()
        else:
            tokens_info = 0.0
        students_list.append({'student_id': obj.student.id, 'token': tokens_info,
                              'name': obj.student.first_name + ' ' + obj.student.last_name})

    return JsonResponse(data={'data': students_list}, safe=False)

