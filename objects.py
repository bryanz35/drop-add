from collections import defaultdict


class Course:
    def __init__(
        self, idx: int, id: str, name: str, schedule: str, max_enrollment: int
    ):
        self.i = idx
        self.id = id
        self.name = name
        self.block = schedule[0]
        self.days = 0  # bitmask
        for i in schedule:
            if i in "12345":
                self.days += 1 << int(i)
        self.max_enrollment = max_enrollment
        self.enrolled = 0

    def __repr__(self):
        return f"Course({self.id}, {self.name}, {self.block}{self.days:05b}, Cap: {self.max_enrollment}, Enrolled: {self.enrolled})"

    def conflict(self, other_course: "Course") -> bool:
        return (self.block == other_course.block) and (
            self.days & other_course.days
        ) > 0


class Student:
    def __init__(
        self,
        id: str,
        schedule: dict[str, int] = defaultdict(int),
    ):
        self.id = int(id[1:])
        self.schedule = schedule

    def __repr__(self):
        return f"Student({self.id}, {self.schedule})"

    def add_course(self, course: Course) -> bool:
        if self.schedule[course.block] & course.days > 0:
            return False
        self.schedule[course.block] |= course.days
        return True
