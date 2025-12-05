import csv
from collections import defaultdict
from pprint import pp

from objects import Course

idx = 0
courses = []
course_dict: dict[str, list[Course]] = defaultdict(list)

with open("courses.csv") as f:
    reader = csv.reader(f)
    next(reader)  # skip headers
    for row in reader:
        courses.append(
            Course(idx, row[3], row[1].split(" ", 1)[1], row[6], int(row[7]))
        )
        course_dict[row[3]].append(courses[-1])
        idx += 1

pp(course_dict)
