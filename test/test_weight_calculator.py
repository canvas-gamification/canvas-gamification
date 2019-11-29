import unittest

from exceptions import RangeValidationException
from weight_calculator import calculate_weights, validate_rages, validate_grades_and_ranges


class WeightCalculatorTest(unittest.TestCase):

    def range_validation_tests(self):
        self.assertFalse(validate_rages({
            "Final": [50, 60],
            "Midterms": [25, 30],
            "Assignments": [0, 5]
        }))

        self.assertFalse(validate_rages({
            "Final": [50, 60],
            "Midterms": [50, 60],
            "Assignments": [10, 15]
        }))

        self.assertFalse(validate_rages({
            "Final": [50, 60],
            "Midterms": [25, 30],
            "Assignments": [15, 10]
        }))

        self.assertTrue(validate_rages({
            "Final": [50, 60],
            "Midterms": [25, 30],
            "Assignments": [5, 15]
        }))

    def range_and_weights_validation_tests(self):
        self.assertFalse(validate_grades_and_ranges(
            {
                "Final": [100, 50],
                "Midterms": [50, 100],
                "Assignments": [100, 0, 100]
            },
            {
                "Final": [50, 60],
                "Midterms": [25, 30],
                "Assignments": [15, 10]
            }))

        self.assertFalse(validate_grades_and_ranges(
            {
                "Finals": [100, 50],
                "Midterms": [50, 100],
                "Assignments": [100, 0, 100]
            },
            {
                "Final": [50, 60],
                "Midterms": [25, 30],
                "Assignments": [10, 15]
            }))

        self.assertFalse(validate_grades_and_ranges(
            {
                "Final": [100, 50],
                "Midterms": [50, 100],
                "Assignments": [100, 0, 100]
            },
            {
                "Finals": [50, 60],
                "Midterms": [25, 30],
                "Assignments": [10, 15]
            }))

        self.assertTrue(validate_grades_and_ranges(
            {
                "Final": [100, 50],
                "Midterms": [50, 100],
                "Assignments": [100, 0, 100]
            },
            {
                "Final": [50, 60],
                "Midterms": [25, 30],
                "Assignments": [10, 15]
            }))

    def test(self):

        ranges = {
            "Final": [50, 60],
            "Midterms": [30, 40],
            "Assignments": [5, 30],
        }

        bad_ranges = {
            "Finals": [50, 60],
            "Midterms": [30, 40],
            "Assignments": [5, 30],
        }

        grades = {
            "Final": [100, 100, 99],
            "Midterms": [50, 60],
            "Assignments": [0, 0, 2, 5, 10]
        }

        weights = calculate_weights(grades, ranges)

        self.assertEqual(weights, {
            "Final": 60,
            "Midterms": 35,
            "Assignments": 5,
        })

        self.assertRaises(RangeValidationException, calculate_weights, bad_ranges, ranges)
