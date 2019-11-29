from exceptions import RangeValidationException


def validate_rages(ranges):
    """
    Validates if weight ranges are feasible

    :param ranges: dict
    {
        "assignment_name": [minimum_percentage, maximum_percentage]
    }
    :return: True if its feasible else False
    """

    min_possible = 0
    max_possible = 0

    for assignment, range_item in ranges.items():
        if range_item[1] < range_item[0]:
            return False
        min_possible += range_item[0]
        max_possible += range_item[1]

    return min_possible <= 100 <= max_possible


def validate_grades_and_ranges(grades, ranges):
    """
    This function validates grades and ranges to check if they are feasible
    and the assignments are identical in grades and ranges

    :param grades: dict
    {
        "assignment_name": [grade1, grade2, ...]
    }
    :param ranges: dict
    {
        "assignment_name": [minimum_percentage, maximum_percentage]
    }
    :return: True if grades and ranges are valid else False
    """

    if not validate_rages(ranges):
        return False

    for assignment, grade in grades.items():
        if assignment not in ranges:
            return False

    for assignment, range_item in ranges.items():
        if assignment not in grades:
            return False
    return True


def calculate_weights(grades, ranges):
    """
    This function calculates best possible choice of weights for a specific students' grades

    :param grades: dict
    {
        "assignment_name": [grade1, grade2, ...]
    }
    :param ranges: dict
    {
        "assignment_name": [minimum_percentage, maximum_percentage]
    }
    :return: dict
    {
        "assignment_name": final_weight
    }
    """

    if not validate_grades_and_ranges(grades, ranges):
        raise RangeValidationException()

    compact_grades = {
        assignment: sum(grade_array) / len(grade_array) for assignment, grade_array in grades.items()
    }

    result = {
        assignment: range_item[0] for assignment, range_item in ranges.items()
    }

    left_over = 100 - sum(weight for assignment, weight in result.items())

    for assignment, grade in sorted(compact_grades.items(), key=lambda x: -x[1]):
        possible_add_weight = ranges[assignment][1] - result[assignment]

        if possible_add_weight <= left_over:
            result[assignment] += possible_add_weight
            left_over -= possible_add_weight
        else:
            result[assignment] += left_over
            left_over = 0

    return result
