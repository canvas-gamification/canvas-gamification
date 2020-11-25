class Canvas(object):
    def __init__(self, base_url, access_token):
        pass

    def get_course(self, course, use_sis_id=False, **kwargs):
        return Course()


class Course(object):
    attributes = {
        'name': 'Mock Course'
    }

    def create_assignment(self, assignment, **kwargs):
        return Assignment()

    def create_assignment_group(self, **kwargs):
        return AssignmentGroup()

    def get_assignment(self, assignment, **kwargs):
        return Assignment()

    def get_users(self, **kwargs):
        return [
            User(1, 'Firstname Lastname', '00000000'),
            User(2, 'multiple student', '12345678'),
            User(3, 'multiple student', '13579135')
        ]

    def submissions_bulk_update(self, **kwargs):
        pass


class AssignmentGroup(object):
    id = 1


class Assignment(object):
    id = 1

    def submissions_bulk_update(self, **kwargs):
        pass


class User(object):
    def __init__(self, id, name, student_id):
        self.id = id
        self.name = name
        self.sis_user_id = student_id
