# -*- coding: utf-8 -*-
import os

import canvasapi
import json

from exceptions import SettingsException, RangeValidationException, RangeFileNotFound
from weight_calculator import calculate_weights, validate_rages


class Canvas:

    @classmethod
    def from_file(cls, settings_file):
        """
        this method creates an instance from a setting file
        :param settings_file: setting file
        :return: and instnce that is created from the setting file
        """
        try:
            settings_dict = json.loads(settings_file.read())
            url = settings_dict['url']
            token = settings_dict['token']
            course_id = settings_dict['course_id']

            weights_ranges_file_name = settings_dict['weights_ranges_file_name']
            weights_ranges_file_local = settings_dict['weights_ranges_file_local']
            weights_assignment_group_name = settings_dict['weights_assignment_group_name']
            weights_assignment_prefix = settings_dict['weights_assignment_prefix']

        except (KeyError, IOError) as e:
            raise SettingsException()

        return cls(url, token, course_id, weights_ranges_file_name, weights_ranges_file_local,
                   weights_assignment_group_name, weights_assignment_prefix)

    def __init__(self, url, token, course_id, weights_ranges_file_name, weights_ranges_file_local,
                 weights_assignment_group_name, weights_assignment_prefix):
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

        self.weights_ranges = self.fetch_weights_ranges_from_local() if weights_ranges_file_local else self.fetch_weights_ranges_from_canvas()

    def fetch_weights_ranges_from_canvas(self):
        """
        get the ranges from the canvas
        looks a file with the name specified in the settings from the files in the canvas website
        :return: dict
            the dictionary of the ranges
            {
                "assignment": [min_percentage, max_percentage]
            }
        """
        files = self.course.get_files()

        weights = None
        for file in files:
            if file.filename == self.weights_ranges_file_name:
                weights = file.get_contents()

        if not weights:
            raise RangeFileNotFound()

        weights = json.loads(weights)

        if not validate_rages(weights):
            raise RangeValidationException()
        return weights

    def fetch_weights_ranges_from_local(self):
        """
        get the ranges from the a file in the project directory
        looks a file with the name specified in the settings from the files in the canvas website
        :return: dict
            the dictionary of the ranges
            {
                "assignment": [min_percentage, max_percentage]
            }
        """
        file = None

        for dirpath, dirnames, filenames in os.walk('.'):
            if self.weights_ranges_file_name in filenames:
                file = open(os.path.join(dirpath, self.weights_ranges_file_name))

        if not file:
            raise RangeFileNotFound()

        weights = json.loads(file.read())

        if not validate_rages(weights):
            raise RangeValidationException()

        return weights

    def get_score(self, assignment, user):
        """
        get the score of a single assignment for a user
        :param assignment: the assignment object
        :param user: user object or user id
        :return: int or float
        """
        score = assignment.get_submission(user).score or 0
        total_score = max(assignment.points_possible, 1)

        return score / total_score

    def get_scores_by_assignment_group_id(self, assignment_group_id, user):
        """
        get all the grades of a user for a specific assignment group
        :param assignment_group_id: int
        :param user: user object or user id
        :return: list
            an array of all the grades received for an assignment group
        """
        assignments = [x for x in self.assignments if x.assignment_group_id == assignment_group_id]
        return [self.get_score(assignment, user) for assignment in assignments]

    def get_all_scores(self, user):
        """
        get all the scores for all the assignment for a user
        :param user: user object or user id
        :return: dict
        {
            "assignment": [grade1, grade 2, ...]
        }
        """
        return {
            assignment_group.name: self.get_scores_by_assignment_group_id(assignment_group.id, user)
            for assignment_group in self.assignment_groups if
            assignment_group.name != self.weights_assignment_group_name
        }

    def get_final_weights(self, user):
        """
        calculates the best possible weights for a user according to the ranges specified in the range file
        :param user: usr object or user id
        :return: dict
        {
            "assignment_name": final_weight
        }
        """
        return calculate_weights(self.get_all_scores(user), self.weights_ranges)

    def get_final_weights_for_all_users(self):
        """
        calculates the best possible weights for all the students according to the ranges specified in the range file
        :return: list
        [
            {
                "user": user id
                "weights": {
                    "assignment_name": final_weight,
                    ...
                }
            }
            ,
            ...
        ]
        """
        return [
            {
                "user": enrol.user['id'],
                "weights": self.get_final_weights(enrol.user['id']),
            } for enrol in self.enrollments if enrol.type == 'StudentEnrollment'
        ]

    def clear_assignment_weights(self):
        """
        delete all the weights assignment
        :return: None
        """
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
        """
        creates the assignment that are used only to see the calculated weights
        :return: list
            list of the created assignments
        """
        weights_assignment_group = self.course.create_assignment_group(name=self.weights_assignment_group_name)
        ranges = self.weights_ranges

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
        """
        The main function of this class
        clear the previous calculated weights
        calculate weights for all the students
        submit them to canvas
        :return: None
        """
        self.clear_assignment_weights()
        weights_assignments = self.create_assignment_weights()
        weights = self.get_final_weights_for_all_users()

        for assignment in weights_assignments:
            grade_data = {}
            for weight in weights:
                grade_data[weight['user']] = {
                    'posted_grade': weight['weights'][assignment.name[len(self.weights_assignment_prefix):]]
                }
            assignment.submissions_bulk_update(grade_data=grade_data)
