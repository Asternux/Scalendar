from datetime import date

from scalendar.core.models import Course, ProjectDocument
from scalendar.core.timetable import iter_course_occurrences, weeks_for_course
from scalendar.core.validation import validate_project


def test_blank_project_has_editable_sections_and_stable_course_id():
    project = ProjectDocument.blank("测试课表")
    course = Course(name="高等数学", weekday=1, start_section=1, end_section=2)
    project.courses.append(course)
    assert len(project.sections) == 12
    assert course.id
    assert validate_project(project) == []


def test_model_round_trip_keeps_course_id_and_fields():
    project = ProjectDocument.blank("秋季课表")
    project.courses.append(Course(id="fixed-course-id", name="大学英语", weekday=2, start_section=3, end_section=4, start_week=2, end_week=18, week_pattern="odd", teacher="王老师", building="外语楼", room="204"))
    restored = ProjectDocument.from_dict(project.to_dict())
    assert restored.project_name == "秋季课表"
    assert restored.courses[0].id == "fixed-course-id"
    assert restored.courses[0].week_pattern == "odd"
    assert restored.courses[0].building == "外语楼"


def test_week_patterns_are_deterministic():
    course = Course(start_week=1, end_week=6, week_pattern="odd")
    assert weeks_for_course(course, 20) == [1, 3, 5]
    course.week_pattern = "even"
    assert weeks_for_course(course, 20) == [2, 4, 6]
    course.week_pattern = "custom"
    course.custom_weeks = [6, 2, 99]
    assert weeks_for_course(course, 20) == [2, 6]


def test_occurrence_date_and_section_times():
    project = ProjectDocument.blank()
    course = Course(id="course-1", name="课", weekday=3, start_section=2, end_section=3, start_week=2, end_week=2)
    occurrences = iter_course_occurrences(project, course)
    assert len(occurrences) == 1
    assert occurrences[0].occurrence_date == date(2026, 9, 16)
    assert occurrences[0].start_time == "08:55"
    assert occurrences[0].end_time == "10:45"
    assert occurrences[0].occurrence_key.startswith("course-1:2026-09-16:")
