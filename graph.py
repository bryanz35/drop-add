import copy
import random

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

    def use(self):
        self.enable = False
        self.other.enable = True


class Vertex:
    def __init__(self, course: Course):
        self.course = course
        self.out: list[Edge] = []


edges = 0


def add_edge(student: Student, start: Course, end: Course, weight: int):
    global edges
    edges += 2
    forward = Edge(student, start, end, weight)
    back = Edge(student, end, start, -weight)
    forward.enable = True
    forward.other = back
    back.other = forward

    vertices[start.i].out.append(forward)
    vertices[end.i].out.append(back)


vertices: list[Vertex] = [Vertex(course) for course in dataloader.courses]
order = list(range(len(vertices)))
MAX_LENGTH = 3  # limit on augmenting path lengths
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


def shuffle():
    """Randomize search order for fairness."""
    random.shuffle(order)
    for vertex in vertices:
        random.shuffle(vertex.out)


def apply_path(path: list[Edge]) -> bool:
    """Augment's the graph with path. Returns false if unsuccessful (conflict)."""
    schedule_new: dict[int, Schedule] = {}
    # process drop
    for e in path:
        if e.student.id not in schedule_new:
            schedule_new[e.student.id] = copy.deepcopy(e.student.schedule)
        schedule_new[e.student.id].toggle(e.start)
    # process add
    for e in path:
        if schedule_new[e.student.id].conflict(e.end):
            return False
        schedule_new[e.student.id].toggle(e.end)

    # apply changes
    for sid, schedule in schedule_new.items():
        dataloader.students[sid].schedule = schedule
    for e in path:
        del e.student.courses[e.start.id]
        e.student.courses[e.end.id] = e.end
    path[0].start.enrolled -= 1
    path[-1].end.enrolled += 1

    return True


def augment(
    start: Vertex, depth: int = MAX_LENGTH, weight: int = 0, path: list[Edge] = []
) -> bool:
    """Find and apply augmenting path (DFS + backtracking)."""

    for edge in start.out:
        if not edge.enable or edge.start.id not in edge.student.courses:
            continue
        path = path + [edge]
        weight_next = weight + edge.weight

        if weight_next > 0 and edge.end.enrolled < edge.end.max_enrollment:
            if apply_path(path):
                return True

        if depth > 1:
            if augment(vertices[edge.end.i], depth - 1, weight_next, path):
                return True

        path.pop()
    return False


def augment_all():
    """Perform augmenting path search for all vertices."""
    changed = False
    print(order)
    for i in order:
        result = augment(vertices[i])
        changed |= result
        if result:
            print(i)
    print("Changed: " + str(changed))
    return changed


if __name__ == "__main__":
    old_schedules = {}
    for student in dataloader.students:
        old_schedules[student.id] = student.courses.copy()

    shuffle()
    while augment_all():
        shuffle()
        pass

    assert dataloader.check_cap()
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
