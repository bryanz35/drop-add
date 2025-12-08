import csv
from collections import defaultdict
from pprint import pp

from objects import Course, Drop, Student

STUDENTS = 680  # upper bound, actual is 673
# edge cases (see README)
BLOCKS = "ABCDEFGHI"  # exclude M block
SKIP_OFFERING = ["MR3080"]
SKIP_REQUESTS = ["HU4410", "HU4480", "CS4120", "AS4052"]

course_idx = 0
courses: list[Course] = []
course_dict: dict[str, dict[int, Course]] = defaultdict(dict)  # id to dict of instances
ignored: set[str] = set()  # list of ignored course IDs
bad_reqs = []


def add_course(row: list[str]):
    global course_idx
    course = Course(
        course_idx, row[3], row[2], row[1].split(" ", 1)[1], row[6], int(row[7])
    )

    if course.block not in BLOCKS:
        ignored.add(row[2])
        return

    courses.append(course)
    course_idx += 1
    course_dict[row[3]][course.instance] = course


with open("courses.csv") as f:
    reader = csv.reader(f)
    next(reader)  # skip headers
    for row in reader:
        if row[3] in SKIP_OFFERING:
            continue
        add_course(row)

# see README
add_course(
    [
        "MA1012 Calculus Ib Exam Prep - MA1012-002",
        "MA1012 Calculus Ib Exam Prep",
        "MA1012-002",
        "MA1012",
        "NCSSM Durham",
        "2nd Semester",
        "H2",
        "99",
    ]
)

students: list[Student] = [Student(i) for i in range(STUDENTS)]
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
        instance = int(row[5][len(row[3]) + 1 :])
        students[id].add_course(course_dict[row[3]][instance])

# exceeds cap
for course in courses:
    course.max_enrollment = max(course.max_enrollment, course.enrolled)

with open("requests.csv") as f:
    reader = csv.reader(f)
    next(reader)  # skip headers
    for row in reader:
        id = int(row[0][1:])
        if row[3] != "None of these apply":
            continue

        def is_none(s: str) -> bool:
            return s == "" or s == "None" or s in SKIP_REQUESTS

        def get_id(i: int) -> str | None:
            id = row[i].split(" ")[0]
            return None if is_none(id) else id

        # valid drop add
        for group in range(4):
            drop = get_id(4 * group + 4)

            main = get_id(4 * group + 5)
            if main == drop:
                main = None
            alts = []
            if (alt := get_id(4 * group + 6)) and alt != drop:
                alts.append(alt)
            if (alt := get_id(4 * group + 7)) and alt != drop:
                alts.append(alt)

            if main is None:
                if alts:
                    main = alts.pop(0)  # bump alt to main
                else:
                    # do not allow only drop -> underload
                    if drop:
                        bad_reqs.append([id] + row[4 * group : 4 * group + 4])
                    continue

            if drop not in students[id].courses:  # see README
                bad_reqs.append(row)
                continue

            students[id].drops.append(Drop(drop, main, alts))


def check_valid_courses() -> bool:
    """Return whether all main+alts exist in course_dict."""
    for i, s in enumerate(students):
        for d in s.drops:
            if any(course not in course_dict for course in [d.main] + d.alts):
                print("INVALID", i, d)
                return False
    return True


def check_no_cycle() -> bool:
    """Return whether a student requests to drop and add the same course."""
    for i, s in enumerate(students):
        drops = set()
        adds = set()
        for d in s.drops:
            drops.add(d.drop)
            for id in [d.main] + d.alts:
                adds.add(id)
        if drops & adds:
            print("CYCLE DETECTED", i)
            pp(s.drops)
            return False
    return True


if __name__ == "__main__":
    print("courses:", len(courses))
    print("distinct:", len(course_dict))
    print("ignored:", ignored)
    print("students with request:", len(list(filter(lambda s: s.drops, students))))
    print("bad requests:", len(bad_reqs))

    assert check_valid_courses()
    assert check_no_cycle()
