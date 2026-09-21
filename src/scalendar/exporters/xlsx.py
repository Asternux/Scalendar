"""Scalendar standard XLSX exporter."""

from __future__ import annotations

from pathlib import Path

from scalendar.core.models import ProjectDocument
from scalendar.core.validation import validate_project
from scalendar.excel.xlsx_io import XlsxError, XlsxWriter


WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
PATTERN_NAMES = {"all": "每周", "odd": "单周", "even": "双周", "custom": "自定义"}
COURSE_HEADERS = [
    "课程名称", "星期", "开始节次", "结束节次", "开始周", "结束周", "周期", "指定周",
    "学校", "校区", "教学楼", "教室", "地点", "教师", "备注",
]


class ExcelExportError(ValueError):
    def __init__(self, code: str, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


def export_project_to_xlsx(project: ProjectDocument, path: str | Path) -> Path:
    issues = validate_project(project)
    if issues:
        raise ExcelExportError("invalid_project", "项目无法导出 Excel：" + "；".join(str(issue) for issue in issues))
    target = Path(path)
    if target.suffix.lower() != ".xlsx":
        target = target.with_suffix(".xlsx")
    courses = [COURSE_HEADERS]
    for course in project.courses:
        courses.append([
            course.name,
            WEEKDAY_NAMES[course.weekday - 1],
            course.start_section,
            course.end_section,
            course.start_week,
            course.end_week,
            PATTERN_NAMES[course.week_pattern],
            ", ".join(str(week) for week in course.custom_weeks),
            project.school,
            project.campus,
            course.building,
            course.room,
            course.location_text,
            course.teacher,
            course.notes,
        ])
    settings = [
        ["设置", "值"],
        ["格式版本", "Scalendar XLSX 1"],
        ["项目名称", project.project_name],
        ["学期名称", project.semester.name],
        ["第一教学周周一", project.semester.first_week_monday],
        ["总周数", project.semester.total_weeks],
        ["学校", project.school],
        ["校区", project.campus],
        [],
        ["节次", "开始时间", "结束时间", "标签"],
    ]
    settings.extend([[section.index, section.start_time, section.end_time, section.label] for section in project.sections])
    writer = XlsxWriter()
    writer.add_sheet(
        "Courses",
        courses,
        widths=[22, 10, 11, 11, 10, 10, 10, 14, 16, 12, 14, 12, 22, 14, 28],
        header_rows=(1,),
        autofilter=True,
    )
    writer.add_sheet(
        "Settings",
        settings,
        widths=[24, 22, 14, 22],
        header_rows=(1, 10),
        autofilter=False,
    )
    try:
        return writer.save(target)
    except XlsxError as exc:
        raise ExcelExportError(exc.code, exc.message, exc.detail) from exc
