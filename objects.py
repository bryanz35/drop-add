from collections import defaultdict
from typing import Optional


class Course:
    def __init__(
        self,
        idx: int,
        id: str,
        id_full: str,
        name: str,
        schedule: str,
        max_enrollment: int,
    ):
        self.i = idx
        self.id = id
        self.instance = int(id_full[len(id) + 1 :])
        self.name = name
        self.block = schedule[0]
        self.days = 0  # bitmask
        for i in range(1, 6):
            if str(i) in schedule:
                self.days += 1 << i
        self.max_enrollment = max_enrollment
        self.enrolled = 0

    def __repr__(self):
        days = str(f"{self.days >> 1:05b}")
        return (
            f"Course({self.id}, {self.instance}, {self.name}, {self.block}{days[::-1]}"
            + f", Cap: {self.max_enrollment}, Enrolled: {self.enrolled})"
        )

    def conflict(self, other_course: "Course") -> bool:
        return (self.block == other_course.block) and (
            self.days & other_course.days
        ) > 0


class Student:
    def __init__(self):
        self.schedule = defaultdict(int)
        self.courses: dict[str, Course] = {}
        self.drops: list[Drop] = []

    def __repr__(self):
        return f"Student({self.courses})"

    def conflict(self, course: Course) -> bool:
        return self.schedule[course.block] & course.days > 0

    def add_course(self, course: Course):
        self.schedule[course.block] |= course.days
        self.courses[course.id] = course
        course.enrolled += 1

    def remove_course(self, course_id: str):
        course = self.courses[course_id]
        self.schedule[course.block] ^= course.days
        del self.courses[course.id]
        course.enrolled -= 1


class Drop:
    def __init__(
        self, main_id: str, alternates_id: list[str] = [], drop: Optional[str] = None
    ):
        self.main = main_id
        self.alts = alternates_id
        self.drop = drop

    def __repr__(self) -> str:
        return f"Drop({self.drop}, {self.main}, {self.alts})"
