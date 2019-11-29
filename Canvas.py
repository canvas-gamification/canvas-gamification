# -*- coding: utf-8 -*-

import canvasapi
import json

from exceptions import SettingsException
from weight_calculator import calculate_weights


class Canvas:

    @classmethod
    def from_file(cls, settings_file):

        try:
            settings_dict = json.loads(settings_file.read())
            url = settings_dict['url']
            token = settings_dict['token']
            course_id = settings_dict['course_id']

            weights_ranges_file_name = settings_dict['weights_ranges_file_name']
            weights_assignment_group_name = settings_dict['weights_assignment_group_name']
            weights_assignment_prefix = settings_dict['weights_assignment_prefix']

        except (KeyError, IOError) as e:
            raise SettingsException()

        return cls(url, token, course_id, weights_ranges_file_name, weights_assignment_group_name,
                   weights_assignment_prefix)

    def __init__(self, url, token, course_id, weights_ranges_file_name, weights_assignment_group_name,
                 weights_assignment_prefix):
        self.url = url
        self.token = token
        self.course_id = course_id
        self.weights_ranges_file_name = weights_ranges_file_name
        self.weights_assignment_group_name = weights_assignment_group_name
        self.weights_assignment_prefix = weights_assignment_prefix

        self.canvas = canvasapi.Canvas(self.url, self.token)
        self.course = self.canvas.get_course(self.course_id)
        self.enrollments = self.course.get_enrollments()
        self.assignments = self.course.get_assignments()
        self.assignment_groups = self.course.get_assignment_groups()

    def get_weights_ranges(self):
        files = self.course.get_files()

        weights = None
        for file in files:
            if file.filename == self.weights_ranges_file_name:
                weights = file.get_contents()
        weights = json.loads(weights)

        return weights

    def get_score(self, assignment, user):
        score = assignment.get_submission(user).score or 0
        total_score = max(assignment.points_possible, 1)

        return score / total_score

    def get_scores_by_assignment_group_id(self, assignment_group_id, user):
        assignments = [x for x in self.assignments if x.assignment_group_id == assignment_group_id]
        return [self.get_score(assignment, user) for assignment in assignments]

    def get_score_array(self, user):
        return {
            assignment_group.name: self.get_scores_by_assignment_group_id(assignment_group.id, user)
            for assignment_group in self.assignment_groups if
        assignment_group.name != self.weights_assignment_group_name
        }

    def get_final_weights(self, user):
        return calculate_weights(self.get_score_array(user), self.get_weights_ranges())

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
            if assignment_group.name == self.weights_assignment_group_name:
                weights_assignment_group = assignment_group
        if not weights_assignment_group:
            return
        for assignment in self.assignments:
            if assignment.assignment_group_id == weights_assignment_group.id:
                assignment.delete()
        weights_assignment_group.delete()

    def create_assignment_weights(self):
        weights_assignment_group = self.course.create_assignment_group(name=self.weights_assignment_group_name)
        ranges = self.get_weights_ranges()

        weights_assignments = []
        for key, val in ranges.items():
            assignment = self.course.create_assignment({
                'points_possible': 100,
                'name': self.weights_assignment_prefix + key,
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
                        'posted_grade': weight['weights'][assignment.name[len(self.weights_assignment_prefix):]]
                    }
                })
