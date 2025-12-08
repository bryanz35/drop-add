import random

import dataloader
from objects import Course, Drop, Student


class Edge:
    def __init__(self, student: Student, drop: Drop, end: Course, weight: int):
        self.student = student
        self.drop = drop
        self.end = end
        self.weight = weight
        self.enable = False
        self.other: Edge


class Vertex:
    def __init__(self, course: Course):
        self.course = course
        self.out: list[Edge] = []


vertices: list[Vertex] = [Vertex(course) for course in dataloader.courses]
MAX_LENGTH = 3  # limit on augmenting path lengths


def add_edge(student: Student, drop: Drop, end: Course, weight: int):
    forward = Edge(student, drop, end, weight)
    back = Edge(student, drop, end, -weight)
    forward.enable = True
    forward.other = back
    back.other = forward

    vertices[student.courses[drop.drop].i].out.append(forward)
    vertices[end.i].out.append(back)


def shuffle() -> list[int]:
    """Randomize search order for fairness."""
    order = list(range(len(vertices)))
    random.shuffle(order)
    for vertex in vertices:
        random.shuffle(vertex.out)
    return order


def augment() -> bool:
    """Find and apply augmenting path."""
    return False
