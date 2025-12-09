import random

import dataloader
from objects import Course, Drop, Student


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
        self.out: list[Edge] = []


def add_edge(student: Student, start: Course, end: Course, weight: int):
    forward = Edge(student, start, end, weight)
    back = Edge(student, end, start, -weight)
    forward.enable = True
    forward.other = back
    back.other = forward

    vertices[start.i].out.append(forward)
    vertices[end.i].out.append(back)


vertices: list[Vertex] = [Vertex(course) for course in dataloader.courses]
order = list(range(len(vertices)))
MAX_LENGTH = 100  # limit on augmenting path lengths
MAIN_WEIGHT = 10
ALT_WEIGHT = 2

for student in dataloader.students:
    for id, course in student.courses.items():
        for _, course_instance in dataloader.course_dict[id].items():
            if course != course_instance:
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


def augment(start: Vertex, depth: int = MAX_LENGTH, weight: int = 0, students=set()) -> bool:
    """Find and apply augmenting path (DFS + backtracking)."""
    # check all paths of length 3
    # check if weight sum is positive
    # check if last course has positive capacity
    # check if block conflicts for any edge
    for edge in start.out:
        if (
            not edge.enable
            or edge.start.id not in edge.student.courses
            or edge.end.id in edge.student.courses
            or edge.student.conflict(edge.end)
            or edge.student in students
        ):
            continue

        edge.student.toggle_course(edge.start, remove=True)
        edge.student.toggle_course(edge.end, remove=False)
        students.add(edge.student)

        weight_next = weight + edge.weight
        if weight_next > 0 and start.course.enrolled < start.course.max_enrollment:
            edge.enable = False
            edge.other.enable = True
            return True
        if depth > 0:
            augment(vertices[edge.end.i], depth - 1, weight_next, students)

        edge.student.toggle_course(edge.start, remove=False)
        edge.student.toggle_course(edge.end, remove=True)
        students.remove(edge.student)
    return False


def augment_all():
    """Perform augmenting path search for all vertices."""
    changed = False
    for i in order:
        result = augment(vertices[i])
        changed |= result
        print(i, result)
    print(changed)