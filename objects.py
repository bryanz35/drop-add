from collections import defaultdict
from pprint import pformat


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
            f"Course({self.id}-{self.instance}, {self.block}{days[::-1]}"
            + f", {self.enrolled}/{self.max_enrollment})"
        )

    def full(self) -> bool:
        return self.enrolled == self.max_enrollment


class Schedule:
    def __init__(self) -> None:
        self.blocks: dict[str, int] = defaultdict(int)

    def conflict(self, course: Course):
        return self.blocks[course.block] & course.days != 0

    def toggle(self, course: Course):
        self.blocks[course.block] ^= course.days


class Student:
    def __init__(self, id: int):
        self.id = id
        self.schedule = Schedule()
        self.courses: dict[str, Course] = {}
        self.drops: list[Drop] = []

    def __repr__(self):
        return f"Student({pformat(self.courses)})"


class Drop:
    def __init__(self, drop: str, main_id: str, alternates_id: list[str] = []):
        self.drop = drop
        self.main = main_id
        self.alts = alternates_id

    def __repr__(self) -> str:
        return f"Drop({self.drop}, main: {self.main}, alts: {self.alts})"
