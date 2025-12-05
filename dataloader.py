import csv
from collections import defaultdict
from pprint import pp

from objects import Course, Student

STUDENTS = 680  # upper bound, actual is 673
BLOCKS = "ABCDEFG"  # we only consider courses in these blocks (ignore M,H,I)

course_idx = 0
courses: list[Course] = []
course_dict: dict[str, list[Course]] = defaultdict(list)
course_pos: dict[str, int] = {}


def add_course(row: list[str]):
    global course_idx
    course = Course(course_idx, row[3], row[1].split(" ", 1)[1], row[6], int(row[7]))

    if course.block not in BLOCKS:
        return

    courses.append(course)
    course_pos[row[2]] = len(course_dict[row[3]])
    course_dict[row[3]].append(course)
    course_idx += 1


with open("courses.csv") as f:
    reader = csv.reader(f)
    next(reader)  # skip headers
    for row in reader:
        add_course(row)

students: list[Student] = [Student() for _ in range(STUDENTS)]
with open("schedules.csv") as f:
    reader = csv.reader(f)
    next(reader)  # skip headers
    for row in reader:
        # skip 1st sem
        if row[6][0] == "1":
            continue
        if row[7][0] not in BLOCKS:
            continue

        id = int(row[0][1:])
        students[id].add_course(course_dict[row[3]][course_pos[row[5]]])

if __name__ == "__main__":
    pp(course_dict)
    pp(students)
