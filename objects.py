class Course:
    def __init__(self, course_id, course_name, schedule, max_enrollment, students=[]):
        self.course_id = course_id
        self.course_name = course_name
        self.schedule = schedule
        self.max_enrollment = max_enrollment
        self.students = students

    def __repr__(self):
        return f"Course({self.course_id}, {self.course_name}, {self.schedule}, {self.max_enrollment}, Enrolled: {len(self.students)})\n"
    
    def enroll_student(self, student):
        if len(self.students) < self.max_enrollment:
            self.students.append(student)
            return True
        else:
            return False
    
    def check_conflict(self, other_course):
        schedule = list(self.schedule)
        course_pattern = list(other_course.schedule)
        if schedule[0] != course_pattern[0]:
            return False
        else:
            for i in range(1, len(schedule)):
                if schedule[i] in course_pattern and schedule[i] != 'L':
                    return True
        return False


class Student:
    def __init__(self, student_id, drop=[], add=[], schedule=[]):
        self.student_id = student_id
        self.drop = drop
        self.add = add
        self.schedule = schedule

    def __repr__(self):
        return f"Student({self.student_id}, Enrolled in: {len(self.schedule)} courses)\n"
    
    def add_course(self, course):
        for scheduled_course in self.schedule:
            if scheduled_course.check_conflict(course):
                return False
        self.schedule.append(course)
        return True