import pandas as pd 
from objects import Course, Student

main_sheet = pd.read_excel("Math Modeling Data Project.xlsx", sheet_name=None)
# print(main_sheet.keys())
# dict_keys(['Spring Course Offerings, Meetin', 'Student Schedules Before DropAd', 'Student Placements', 'DropAdd Requests'])
# print(main_sheet['Spring Course Offerings, Meetin'])
# course_ids = main_sheet['Spring Course Offerings, Meetin'].iloc[:, 0].tolist()
# course_names = main_sheet['Spring Course Offerings, Meetin'].iloc[:, 1].tolist()
# course_meetin
courses = []
course_dict = {}

for index, row in main_sheet['Spring Course Offerings, Meetin'].iloc[1:].iterrows():
    courses.append(Course(
        row[3],
        row[1],
        row[6],
        row[7]
    ))
    course_dict[row[3]] = [course_dict.get(row[3], []) , courses[-1]][-1]
# note: research courses can meet F and G block, but we should not consider them for dropadd anyway and they are ignored. 
print(courses)
print(course_dict)
student_sheet = main_sheet['Student Schedules Before DropAd']
# print(student_sheet)