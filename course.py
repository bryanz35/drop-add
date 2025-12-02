class Course:
    def __init__(self, course_id, course_name, schedule, max_enrollment, students=[]):
        self.course_id = course_id
        self.course_name = course_name
        self.schedule = schedule
        self.max_enrollment = max_enrollment
        self.students = students

    def __repr__(self):
        return f"Course({self.course_id}, {self.course_name}, {self.schedule}, {self.max_enrollment}, Enrolled: {len(self.students)})"
    
    def enroll_student(self, student):
        if len(self.students) < self.max_enrollment:
            self.students.append(student)
            return True
        else:
            return False
    
    def check_conflict(self, other_course):
        # TODO: check for gaps in schedule (G124L and G3)
        return bool(set(self.schedule) & set(other_course.schedule))