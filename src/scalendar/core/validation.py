"""Validation rules for project files and user-editable timetable values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re

from .models import ProjectDocument

TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
PATTERNS = {"all", "odd", "even", "custom"}


def parse_custom_weeks(value: str, total_weeks: int, *, required: bool = False) -> list[int]:
    """Parse the compact custom-week input used by the editor.

    The parser is deliberately strict so a typo cannot be silently discarded
    while saving a course. Chinese commas are accepted because they are common
    in Chinese input methods.
    """

    text = str(value or "").strip().replace("，", ",")
    if not text:
        if required:
            raise ValueError("自定义周次不能为空")
        return []
    tokens = [token.strip() for token in text.split(",")]
    if any(not token for token in tokens):
        raise ValueError("自定义周次请使用逗号分隔，例如 1,3,5")
    weeks: list[int] = []
    for token in tokens:
        if not token.isdigit():
            raise ValueError(f"自定义周次“{token}”不是有效数字")
        week = int(token)
        if week < 1 or week > total_weeks:
            raise ValueError(f"自定义周次必须在 1 到 {total_weeks} 周之间")
        if week in weeks:
            raise ValueError(f"自定义周次 {week} 重复")
        weeks.append(week)
    return sorted(weeks)


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def validate_project(project: ProjectDocument) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    semester = project.semester
    try:
        monday = date.fromisoformat(semester.first_week_monday)
        if monday.weekday() != 0:
            issues.append(ValidationIssue("semester.first_week_monday", "必须是周一"))
    except ValueError:
        issues.append(ValidationIssue("semester.first_week_monday", "必须是 YYYY-MM-DD 日期"))
    if not 1 <= semester.total_weeks <= 60:
        issues.append(ValidationIssue("semester.total_weeks", "应在 1 到 60 周之间"))
    if not semester.timezone.strip():
        issues.append(ValidationIssue("semester.timezone", "不能为空"))

    seen_sections: set[int] = set()
    for position, section in enumerate(project.sections):
        path = f"sections[{position}]"
        if section.index <= 0:
            issues.append(ValidationIssue(f"{path}.index", "必须为正整数"))
        if section.index in seen_sections:
            issues.append(ValidationIssue(f"{path}.index", "节次编号不能重复"))
        seen_sections.add(section.index)
        if not TIME_RE.fullmatch(section.start_time):
            issues.append(ValidationIssue(f"{path}.start_time", "格式应为 HH:MM"))
        if not TIME_RE.fullmatch(section.end_time):
            issues.append(ValidationIssue(f"{path}.end_time", "格式应为 HH:MM"))
        if TIME_RE.fullmatch(section.start_time) and TIME_RE.fullmatch(section.end_time) and section.start_time >= section.end_time:
            issues.append(ValidationIssue(path, "结束时间必须晚于开始时间"))

    section_ids = seen_sections
    seen_course_ids: set[str] = set()
    for position, course in enumerate(project.courses):
        path = f"courses[{position}]"
        if not course.id:
            issues.append(ValidationIssue(f"{path}.id", "课程必须有稳定 ID"))
        if course.id in seen_course_ids:
            issues.append(ValidationIssue(f"{path}.id", "课程 ID 不能重复"))
        seen_course_ids.add(course.id)
        if not course.name.strip():
            issues.append(ValidationIssue(f"{path}.name", "课程名称不能为空"))
        if not 1 <= course.weekday <= 7:
            issues.append(ValidationIssue(f"{path}.weekday", "星期应为 1 到 7"))
        if course.start_section > course.end_section:
            issues.append(ValidationIssue(path, "结束节次不能早于开始节次"))
        if course.start_section not in section_ids or course.end_section not in section_ids:
            issues.append(ValidationIssue(path, "课程使用了未配置的节次"))
        elif any(section_index not in section_ids for section_index in range(course.start_section, course.end_section + 1)):
            issues.append(ValidationIssue(path, "课程范围中包含未配置的中间节次"))
        if not 1 <= course.start_week <= semester.total_weeks:
            issues.append(ValidationIssue(f"{path}.start_week", "起始周超出学期范围"))
        if not 1 <= course.end_week <= semester.total_weeks:
            issues.append(ValidationIssue(f"{path}.end_week", "结束周超出学期范围"))
        if course.start_week > course.end_week:
            issues.append(ValidationIssue(path, "结束周不能早于起始周"))
        if course.week_pattern not in PATTERNS:
            issues.append(ValidationIssue(f"{path}.week_pattern", "只支持 all、odd、even、custom"))
        if course.week_pattern == "custom" and not course.custom_weeks:
            issues.append(ValidationIssue(f"{path}.custom_weeks", "自定义周次不能为空"))
        if len(course.custom_weeks) != len(set(course.custom_weeks)):
            issues.append(ValidationIssue(f"{path}.custom_weeks", "自定义周次不能重复"))
        if any(week < 1 or week > semester.total_weeks for week in course.custom_weeks):
            issues.append(ValidationIssue(f"{path}.custom_weeks", "自定义周必须在学期范围内"))
    return issues
