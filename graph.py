import copy
import random
from collections import defaultdict

import dataloader
from objects import Course, Student


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
        self.indeg: list[Edge] = []


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

    vertices[start.i].indeg.append(back)
    vertices[end.i].indeg.append(forward)


vertices: list[Vertex] = [Vertex(course) for course in dataloader.courses]
MAX_LENGTH = 2  # limit on augmenting path lengths
MAIN_WEIGHT = 50
ALT_WEIGHT = 10
SWAP_WEIGHT = -1

for student in dataloader.students:
    # add edges for course swaps
    for id, course in student.courses.items():
        swap_family = EdgeFamily()
        for _, course_instance in dataloader.course_dict[id].items():
            if (
                course.block != course_instance.block
                or course.days != course_instance.days
            ):
                add_edge(swap_family, student, course, course_instance, SWAP_WEIGHT)

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
        random.shuffle(vertex.indeg)

    order = list(range(len(dataloader.courses)))
    random.shuffle(order)
    return order


def apply_path(path: list[Edge]) -> bool:
    """Augment's the graph with path. Returns false if unsuccessful (conflict)."""
    # group edges by student
    student_edges: dict[Student, list[Edge]] = defaultdict(list)
    for edge in path:
        student_edges[edge.student].append(edge)

    # process adds
    for student, edges in student_edges.items():
        schedule = copy.deepcopy(student.schedule)
        courses = student.courses.copy()
        for edge in edges:
            if schedule.conflict(edge.end) or edge.end.id in courses:
                return False
            schedule.toggle(edge.end)

    # apply changes
    for edge in path:
        edge.student.add(edge.end)
        edge.start.enrolled -= 1
        edge.end.enrolled += 1

    print(list(reversed(path)))
    assert dataloader.check_enrollment()
    return True


def augment(
    end: Vertex, depth: int, weight: int, path: list[Edge], prev: Edge | None
) -> bool:
    """Find and apply augmenting path (DFS + backtracking)."""
    for edge in end.indeg:
        if (
            (prev and edge == prev.other)  # don't undo previous edge
            or not edge.enable
            or (edge.primary and edge.family.used)
            or not edge.student.has(edge.start.id)
        ):
            continue

        # add edge to current path
        path = path + [edge]
        weight_next = weight + edge.weight
        edge.student.remove(edge.start)
        edge.family.used = edge.primary
        edge.enable = False
        edge.other.enable = True

        # try current path
        if weight_next > 0 and path[0].end.has_space():
            if apply_path(path):
                return True

        # extend path
        if depth > 1:
            if augment(vertices[edge.start.i], depth - 1, weight_next, path, edge):
                return True

        # backtrack
        edge.other.enable = False
        edge.enable = True
        edge.family.used = not edge.primary
        edge.student.add(edge.start)
        path.pop()
    return False


def augment_all(order: list[int]):
    """Perform augmenting path search for all vertices."""
    changed = False
    for i in order:
        if augment(vertices[i], MAX_LENGTH, 0, [], None):
            changed = True
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
        for student in dataloader.students:
            print(student, file=f)
