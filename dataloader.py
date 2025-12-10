import csv
from collections import defaultdict

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
blacklist: set[int] = set()
good_reqs = 0


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
        course = course_dict[row[3]][instance]
        if students[id].conflict(course):
            blacklist.add(id)
        else:
            students[id].toggle_course(course, remove=False)

# increase caps for courses that currently exceed cap
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

        # valid drop add
        for group in range(4):
            request = row[4 * group + 4 : 4 * group + 8]
            if id in blacklist:
                bad_reqs.append([id] + request)
                continue

            def get_id(i: int, drop=False) -> str | None:
                cid = request[i].split(" ")[0]
                return (
                    None
                    if is_none(cid) or (not drop and cid in students[id].courses)
                    else cid
                )

            drop = get_id(0, True)
            main = get_id(1)
            if main == drop:
                main = None
            alts = []
            if (alt := get_id(2)) and alt != drop:
                alts.append(alt)
            if (alt := get_id(3)) and alt != drop:
                alts.append(alt)

            if main is None:
                if alts:
                    main = alts.pop(0)  # bump alt to main
                else:
                    # do not allow only drop -> underload
                    if drop:
                        bad_reqs.append([id] + request)
                    continue

            if drop not in students[id].courses:  # see README
                bad_reqs.append([id] + request)
                continue
            good_reqs += 1
            students[id].drops.append(Drop(drop, main, alts))

students_with_requests = len(list(filter(lambda s: s.drops, students)))


def check_valid_courses() -> bool:
    """Check whether all main+alts exist in course_dict and not their courses."""
    for i, s in enumerate(students):
        for d in s.drops:
            if any(
                course not in course_dict or course in s.courses
                for course in [d.main] + d.alts
            ):
                print("INVALID", i, d)
                return False
    return True


def check_no_block_conflict(student: Student) -> bool:
    """Check whether a student's schedule has block conflicts."""
    if student.id in blacklist:
        return True

    schedule = defaultdict(int)
    for course in student.courses.values():
        if schedule[course.block] & course.days != 0:
            print("BLOCK CONFLICT", id, student.courses)
            return False
        schedule[course.block] |= course.days
    return True


def check_no_block_conflicts() -> bool:
    """Check whether any student's schedule has block conflicts."""
    for student in students:
        if not check_no_block_conflict(student):
            return False
    return True


if __name__ == "__main__":
    print("courses:", len(courses))
    print("distinct:", len(course_dict))
    print("ignored:", ignored)
    print("blacklist:", len(blacklist))
    print("students with request:", students_with_requests)
    print("good requests:", good_reqs)
    print("bad requests:", len(bad_reqs))

    assert check_valid_courses()
    assert check_no_block_conflicts()
