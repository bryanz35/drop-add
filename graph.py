import copy
import random
from collections import defaultdict

import dataloader
from objects import Course, Schedule, Student


class EdgeFamily:
    def __init__(self):
        self.used = False


class Edge:
    def __init__(
        self,
        family: EdgeFamily,
        student: Student,
        start: Course,
        end: Course,
        weight: int,
    ):
        self.family = family
        self.primary = False
        self.student = student
        self.start = start
        self.end = end
        self.weight = weight
        self.enable = False
        self.other: Edge

    def __repr__(self) -> str:
        return f"Edge({self.student.id}, {self.start}, {self.end}, {self.weight}, {self.enable})"


class Vertex:
    def __init__(self, course: Course):
        self.course = course
        self.out: list[Edge] = []


edges = 0


def add_edge(
    family: EdgeFamily, student: Student, start: Course, end: Course, weight: int
):
    global edges
    edges += 2
    forward = Edge(family, student, start, end, weight)
    back = Edge(family, student, end, start, -weight)
    forward.enable = True
    forward.primary = True
    forward.other = back
    back.other = forward

    vertices[start.i].out.append(forward)
    vertices[end.i].out.append(back)


vertices: list[Vertex] = [Vertex(course) for course in dataloader.courses]
MAX_LENGTH = 6  # limit on augmenting path lengths
MAIN_WEIGHT = 10
ALT_WEIGHT = 2

for student in dataloader.students:
    # add edges from each drop
    for drop in student.drops:
        drop_instance = student.courses[drop.drop]
        main = dataloader.course_dict[drop.main]
        drop_family = EdgeFamily()
        for _, main_instance in main.items():
            add_edge(
                drop_family,
                student,
                drop_instance,
                main_instance,
                MAIN_WEIGHT,
            )
        for alt_id in drop.alts:
            alt = dataloader.course_dict[alt_id]
            for _, alt_instance in alt.items():
                add_edge(
                    drop_family,
                    student,
                    drop_instance,
                    alt_instance,
                    ALT_WEIGHT,
                )


random.seed(1434)


def shuffle() -> list[int]:
    """Randomize search order for fairness."""
    for vertex in vertices:
        random.shuffle(vertex.out)

    order = list(range(len(dataloader.courses)))
    random.shuffle(order)
    return order


def find_patch(
    schedule: Schedule, courses: dict[str, Course], bad: Course
) -> tuple[Course, Course] | None:
    """Try to apply swap patch when bad conflicts with schedule."""
    # find courses that conflict
    conflicts = []
    for course in courses.values():
        if course.conflict(bad):
            conflicts.append(course)

    # we don't care about patching more than once
    if len(conflicts) > 1:
        return None

    assert conflicts, (schedule, courses, bad)  # conflicts shouldn't be empty
    course = conflicts[0]
    # find swaps
    for cswap in dataloader.course_dict[course.id].values():
        if bad.conflict(cswap) or schedule.conflict(cswap):
            continue

        # apply patch
        if cswap.has_space():
            courses[course.id] = cswap
            schedule.toggle(course)
            schedule.toggle(cswap)
            return course, cswap

    return None


def apply_path(path: list[Edge]) -> bool:
    """Augment's the graph with path. Returns false if unsuccessful (conflict)."""
    # group edges by student
    student_edges: dict[Student, list[Edge]] = defaultdict(list)
    for edge in path:
        student_edges[edge.student].append(edge)

    # process adds
    patches: list[tuple[Course, Course]] = []
    updates: list[tuple[Schedule, dict[str, Course]]] = []
    for student, edges in student_edges.items():
        schedule = copy.deepcopy(student.schedule)
        courses = student.courses.copy()
        for edge in edges:
            if edge.end.id in courses:
                return False
            if schedule.conflict(edge.end):
                patch = find_patch(schedule, courses, edge.end)
                if patch is None:
                    return False
                patches.append(patch)

            schedule.toggle(edge.end)
            courses[edge.end.id] = edge.end
        schedule.assert_sync(courses)
        updates.append((schedule, courses))

    # apply changes to schedules, courses, and enrollments
    for i, (student, edges) in enumerate(student_edges.items()):
        student.schedule, student.courses = updates[i]
        for edge in edges:
            edge.start.enrolled -= 1
            edge.end.enrolled += 1
    for course, cswap in patches:
        course.enrolled -= 1
        cswap.enrolled += 1

    assert dataloader.check_enrollment()
    return True


def augment(start: Vertex, depth: int, weight: int, path: list[Edge]) -> bool:
    """Find and apply augmenting path (DFS + backtracking)."""
    for edge in start.out:
        same_family_as_last = path and path[-1].family == edge.family
        if (
            (path and edge == path[-1].other)  # don't undo previous edge
            or not edge.enable
            or (edge.primary and edge.family.used and not same_family_as_last)
            or not edge.student.has_course(edge.start)
        ):
            continue

        # add edge to current path
        path = path + [edge]
        weight_next = weight + edge.weight
        edge.student.remove(edge.start)
        edge.family.used = edge.primary
        edge.enable = False
        edge.other.enable = True
        edge.student.schedule.assert_sync(edge.student.courses)

        # try current path
        if weight_next > 0 and path[-1].end.has_space():
            if apply_path(path):
                return True

        # extend path
        if depth > 1:
            if augment(vertices[edge.end.i], depth - 1, weight_next, path):
                return True

        # backtrack
        edge.other.enable = False
        edge.enable = True
        edge.family.used = not edge.primary
        edge.student.add(edge.start)
        assert edge.start.enrolled <= edge.start.max_enrollment
        path.pop()
    return False


def augment_all(order: list[int]):
    """Perform augmenting path search for all vertices."""
    changed = False
    for i in order:
        if augment(vertices[i], MAX_LENGTH, 0, []):
            changed = True
            print(i)
        assert dataloader.check_enrollment()
    print("Changed: " + str(changed))
    return changed


if __name__ == "__main__":
    old_schedules = {}
    for student in dataloader.students:
        old_schedules[student.id] = student.courses.copy()

    while augment_all(shuffle()):
        pass

    assert dataloader.check_enrollment()
    assert dataloader.check_no_block_conflicts()

    new_schedules = {}
    for student in dataloader.students:
        new_schedules[student.id] = student.courses.copy()

    fulfilled_requests = 0
    unfulfilled_students = 0
    conflict_ids = set()
    for i, student in enumerate(dataloader.students):
        if not student.drops:
            continue
        fulfilled = False
        for drop in student.drops:
            if not student.has_id(drop.drop):
                fulfilled_requests += 1
                fulfilled = True
        if not fulfilled:
            unfulfilled_students += 1

    swr = dataloader.students_with_requests
    fraction_fullfilled = (swr - unfulfilled_students) / swr
    print("-" * 80)
    print(f"Edges: {edges}")
    print(f"Filled {fulfilled_requests} out of {dataloader.good_reqs} requests.")
    print(f"Students with requests considered: {swr}.")
    print(f"There were {unfulfilled_students} students with no request satisfied.")
    print(f"{fraction_fullfilled:.2%} of students got at least 1 request satisfied.")
    print(f"Hall of shame: {sorted(dataloader.blacklist)}.")

    with open("processed.json", "w") as f:
        for student in dataloader.students:
            print(student, file=f)
