import csv
from collections import defaultdict
from pprint import pp

from objects import Course, Student, Drop

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


with open("requests.csv") as f:
    reader = csv.reader(f)
    next(reader)  # skip headers
    for row in reader:
        id = int(row[0][1:])
        if row[3] != "None of these apply":
            continue

        def is_none(s: str) -> bool:
            return s == "" or s[:4] == "None"

        def get_id(i: int) -> str:
            return row[i].split(" ")[0]

        # valid drop add
        for group in range(4):
            drop = None if is_none(row[4 * group + 4]) else get_id(4 * group + 4)
            main = None if is_none(row[4 * group + 5]) else get_id(4 * group + 5)
            alts = []
            if not is_none(row[4 * group + 6]):
                alts.append(get_id(4 * group + 6))
            if not is_none(row[4 * group + 7]):
                alts.append(get_id(4 * group + 7))

            if main is None:
                if alts:
                    main = alts.pop(0)
                elif drop: # only drop, no add
                    students[id].remove_course(drop)
                    continue
                else: # empty request
                    continue

            # has main add
            students[id].drop.append(Drop(main, alts, drop))


if __name__ == "__main__":
    # pp(course_dict)
    # pp(students)
    print(len(course_dict))