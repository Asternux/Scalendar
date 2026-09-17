"""Date and time expansion for recurring courses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .models import Course, ProjectDocument, Section


@dataclass(frozen=True)
class CourseOccurrence:
    course_id: str
    occurrence_key: str
    course_name: str
    occurrence_date: date
    start_time: str
    end_time: str
    location_text: str


def weeks_for_course(course: Course, total_weeks: int) -> list[int]:
    candidates = range(course.start_week, course.end_week + 1)
    if course.week_pattern == "odd":
        return [week for week in candidates if week % 2 == 1]
    if course.week_pattern == "even":
        return [week for week in candidates if week % 2 == 0]
    if course.week_pattern == "custom":
        selected = set(course.custom_weeks)
        return [week for week in candidates if week in selected]
    return list(candidates)


def _section_map(project: ProjectDocument) -> dict[int, Section]:
    return {section.index: section for section in project.sections}


def iter_course_occurrences(project: ProjectDocument, course: Course) -> list[CourseOccurrence]:
    sections = _section_map(project)
    start = sections[course.start_section]
    end = sections[course.end_section]
    first_monday = project.semester_start()
    occurrences: list[CourseOccurrence] = []
    for week in weeks_for_course(course, project.semester.total_weeks):
        occurrence_date = first_monday + timedelta(weeks=week - 1, days=course.weekday - 1)
        key = f"{course.id}:{occurrence_date.isoformat()}:{start.start_time}-{end.end_time}"
        occurrences.append(CourseOccurrence(course_id=course.id, occurrence_key=key, course_name=course.name, occurrence_date=occurrence_date, start_time=start.start_time, end_time=end.end_time, location_text=course.location_text))
    return occurrences
