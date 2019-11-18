# -*- coding: utf-8 -*-

import canvasapi
import json

from Course import Course


class Canvas:
    def __init__(self, url=None, token=None, course_id=None):
        self.url = 'https://canvas.ubc.ca'
        self.token = "11224~t93W3Ig73DPLI6nUZ61g1PAt1uGWixRzzVtIvI9B56szfNzTIypROPJyYcXV39JQ"
        self.course_id = 45950

        self.canvas = canvasapi.Canvas(self.url, self.token)
        self.course = self.canvas.get_course(self.course_id)
        self.enrollments = self.course.get_enrollments()
        self.assignments = self.course.get_assignments()
        self.assignment_groups = self.course.get_assignment_groups()

    def get_weights_ranges(self):
        files = self.course.get_files()

        weights = None
        for file in files:
            if file.filename == 'Weights.txt':
                weights = file.get_contents()
        weights = json.loads(weights)

        return weights

    def get_score(self, assignment, user):
        score = assignment.get_submission(user).score or 0
        # print(("*" * 10), score, user, assignment.name)
        total_score = max(assignment.points_possible, 1)

        return score / total_score

    def get_scores_by_assignment_group_id(self, assignment_group_id, user):
        assignments = [x for x in self.assignments if x.assignment_group_id == assignment_group_id]
        return [self.get_score(assignment, user) for assignment in assignments]

    def get_score_array(self, user):
        return {
            assignment_group.name: self.get_scores_by_assignment_group_id(assignment_group.id, user)
            for assignment_group in self.assignment_groups if assignment_group.name != 'Weights'
        }

    def get_final_weights(self, user):
        ranges = self.get_weights_ranges()
        ranges = [[key, val[0], val[1]] for key, val in ranges.items()]

        c = Course(0, ranges)

        scores = self.get_score_array(user)
        scores = [[key] + val for key, val in scores.items()]

        return {
            x[0]: x[1]
            for x in c.get_percentages(scores)
        }

    def get_final_weights_for_all_users(self):
        return [
            {
                "user": enrol.user['id'],
                "weights": self.get_final_weights(enrol.user['id']),
            } for enrol in self.enrollments if enrol.type == 'StudentEnrollment'
        ]

    def clear_assignment_weights(self):
        weights_assignment_group = None
        for assignment_group in self.assignment_groups:
            if assignment_group.name == "Weights":
                weights_assignment_group = assignment_group
        if not weights_assignment_group:
            return
        for assignment in self.assignments:
            if assignment.assignment_group_id == weights_assignment_group.id:
                assignment.delete()
        weights_assignment_group.delete()

    def create_assignment_weights(self):
        weights_assignment_group = self.course.create_assignment_group(name="Weights")
        ranges = self.get_weights_ranges()

        weights_assignments = []
        for key, val in ranges.items():
            assignment = self.course.create_assignment({
                'points_possible': 100,
                'name': key,
                'assignment_group_id': weights_assignment_group.id,
                'published': True,
            })
            weights_assignments.append(assignment)
        return weights_assignments

    def assign_weights(self):
        self.clear_assignment_weights()
        weights_assignments = self.create_assignment_weights()
        weights = self.get_final_weights_for_all_users()

        for assignment in weights_assignments:
            for weight in weights:
                assignment.submissions_bulk_update(grade_data={
                    weight['user']: {
                        'posted_grade': weight['weights'][assignment.name]
                    }
                })
