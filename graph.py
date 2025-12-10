import copy
import json
import random
from collections import defaultdict

import dataloader
from objects import Course, Schedule, Student


class Edge:
    def __init__(self, student: Student, start: Course, end: Course, weight: int):
        self.student = student
        self.start = start
        self.end = end
        self.weight = weight
        self.enable = False
        self.other: Edge


class Vertex:
    def __init__(self, course: Course):
        self.course = course
        self.indeg: list[Edge] = []


edges = 0


def add_edge(student: Student, start: Course, end: Course, weight: int):
    global edges
    edges += 2
    forward = Edge(student, start, end, weight)
    back = Edge(student, end, start, -weight)
    forward.enable = True
    forward.other = back
    back.other = forward

    vertices[start.i].indeg.append(back)
    vertices[end.i].indeg.append(forward)


vertices: list[Vertex] = [Vertex(course) for course in dataloader.courses]
MAX_LENGTH = 2  # limit on augmenting path lengths
MAIN_WEIGHT = 10
ALT_WEIGHT = 2

for student in dataloader.students:
    for id, course in student.courses.items():
        for _, course_instance in dataloader.course_dict[id].items():
            if (
                course.block != course_instance.block
                or course.days != course_instance.days
            ):
                add_edge(student, course, course_instance, 0)

    for drop in student.drops:
        drop_course = student.courses[drop.drop]
        main = dataloader.course_dict[drop.main]
        for _, main_instance in main.items():
            add_edge(student, student.courses[drop.drop], main_instance, MAIN_WEIGHT)
        for alt_id in drop.alts:
            alt = dataloader.course_dict[alt_id]
            for _, alt_instance in alt.items():
                add_edge(student, student.courses[drop.drop], alt_instance, ALT_WEIGHT)


random.seed(1434)


def shuffle() -> list[int]:
    """Randomize search order for fairness."""
    for vertex in vertices:
        random.shuffle(vertex.indeg)

    order = list(range(len(dataloader.courses)))
    random.shuffle(order)
    return order


def apply_path(path: list[Edge]) -> bool:
    """Augment's the graph with path. Returns false if unsuccessful (conflict)."""
    # process add
    student_edges: dict[Student, list[Edge]] = defaultdict(list)
    for edge in path:
        student_edges[edge.student].append(edge)

    updates: list[tuple[Schedule, dict[str, Course]]] = []
    for student, edges in student_edges.items():
        schedule = copy.deepcopy(student.schedule)
        courses = copy.deepcopy(student.courses)
        for edge in edges:
            if schedule.conflict(edge.end) or edge.end.id in courses:
                return False
            schedule.toggle(edge.end)
            courses[edge.end.id] = edge.end
        updates.append((schedule, courses))

    # apply changes
    for i, student in enumerate(student_edges):
        student.schedule = updates[i][0]
        student.courses = updates[i][1]
    for edge in path:
        edge.enable = False
        edge.other.enable = True
    path[0].end.enrolled += 1
    path[-1].start.enrolled -= 1

    return True


def augment(
    end: Vertex, depth: int = MAX_LENGTH, weight: int = 0, path: list[Edge] = []
) -> bool:
    """Find and apply augmenting path (DFS + backtracking)."""
    for edge in end.indeg:
        if not edge.enable or edge.start.id not in edge.student.courses:
            continue

        path = path + [edge]
        weight_next = weight + edge.weight
        edge.student.schedule.toggle(edge.start)
        del edge.student.courses[edge.start.id]

        if weight_next > 0 and path[0].end.has_space():
            if apply_path(path):
                return True

        if depth > 1:
            if augment(vertices[edge.start.i], depth - 1, weight_next):
                return True

        # backtrack
        path.pop()
        edge.student.schedule.toggle(edge.start)
        edge.student.courses[edge.start.id] = edge.start
    return False


def augment_all(order: list[int]):
    """Perform augmenting path search for all vertices."""
    changed = False
    for i in order:
        if augment(vertices[i]):
            changed = True
            print(i)
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
        old = set(old_schedules[i].values())
        new = set(new_schedules[i].values())
        if old == new:
            if student.drops:
                unfulfilled_students += 1
            continue

        removed = old - new
        added = new - old

        # print("-" * 80)
        # print(f"Student {i}:")
        # print(f"Dropped: {removed}")
        # print(f"Added: {added}")
        # print(f"Requests: {student.drops}")

        # check if there is a course conflict in new schedule
        # 135 our error
        assert len(removed) == len(added), f"Student {i} cooked"
        fulfilled_requests += len(removed)

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
        json.dump(dataloader.students, f)
