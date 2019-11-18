class Course:
    """
    "Course" is a class that is used to model the system of grades for
    a given course. It has a course code along with the types of
    assignments and their given grade ranges.
    """

    def __init__(self, course_code, types_and_ranges):
        """
        The class initiliazation.

        Parameters:
        -----------
        course_code : str
            The string that uniquely identifies a given Course.
        types_and_ranges : arr
            An array of arrays. The first element is the type,
            followed by the minimum grade in the range, and then the
            maximum grade in the range.
        """
        self.course_code = course_code
        self.types_and_ranges = types_and_ranges

    def get_percentages(self, types_and_grades):
        """
        This method takes in an array of assignment types and the grades
        received for each assignment, and then spits out the best
        percentage for each assignment type based on the grades and
        ranges.

        Parameters:
        -----------
        types_and_grades : arr
            An array of arrays. The first element is the
            assignment type, followed by the grades received for each
            assignment under that type.

        Returns:
        --------
        types_and_percentages : arr
            A array of tuples where the first element is the assignment
            type and the second is the optimized grade percentage.
        """

        # Get the average grades, and sort by highest to lowest
        types_and_averages = self.find_grade_averages(types_and_grades)
        types_and_averages.sort(reverse=True, key=lambda x: x[1])

        # Sort the types_and_ranges into the same order
        type_order = []
        for each in types_and_averages:
            type_order.append(each[0])
        types_and_ranges = [
            tuple for x in type_order for tuple in self.types_and_ranges if tuple[0] == x]
        reversed(types_and_ranges)

        # Set the min percentage that the totals cannot drop below,
        # also set max percentage to be 100
        max = 100
        min = 0
        for each in self.types_and_ranges:
            min += int(each[1])

        # Determine percentages
        types_and_percentages = []
        for i, each in enumerate(types_and_ranges):
            type_and_percentage = [each[0]]
            range_min = int(each[1])
            range_max = int(each[2])
            min -= range_min
            perc = max - min
            # print("r_max: " + str(range_max))
            # print("perc: " + str(perc))
            if range_max < perc:
                perc = range_max
            type_and_percentage.append(perc)
            max -= perc
            types_and_percentages.append(type_and_percentage)
            # print()
        return types_and_percentages

    def find_grade_averages(self, types_and_grades):
        """
        Get the averages for each assignment type.

        Parameters:
        -----------
        types_and_grades : arr
            An array of arrays. The first element is the
            assignment type, followed by the grades received for each
            assignment under that type.

        Returns:
        --------
        types_and_averages : arr
            A array of tuples where the first element is the assignment
            type and the second is the grade average.

        """
        types_and_averages = []
        for e in types_and_grades:
            type_and_average = [e[0]]
            total_grade = 0
            for i in range(1, len(e)):
                total_grade += float(e[i])
            avg_grade = total_grade / (len(e) - 1)
            type_and_average.append(avg_grade)
            types_and_averages.append(type_and_average)
        return types_and_averages

