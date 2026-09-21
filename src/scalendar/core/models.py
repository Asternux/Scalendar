"""The stable, serializable data model for a Scalendar project.

The model intentionally contains no Qt or UI types. That keeps project files
portable and makes date calculations and validation straightforward to test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = 1


def new_id() -> str:
    """Return a stable identifier for a newly created course."""

    return str(uuid4())


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class Semester:
    name: str = "未命名学期"
    first_week_monday: str = "2026-09-07"
    total_weeks: int = 20
    timezone: str = "Asia/Shanghai"

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "first_week_monday": self.first_week_monday, "total_weeks": self.total_weeks, "timezone": self.timezone}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Semester":
        data = data or {}
        return cls(name=str(data.get("name", "未命名学期")), first_week_monday=str(data.get("first_week_monday", "2026-09-07")), total_weeks=_as_int(data.get("total_weeks"), 20), timezone=str(data.get("timezone", "Asia/Shanghai")))


@dataclass
class Section:
    index: int
    start_time: str
    end_time: str
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"index": self.index, "start_time": self.start_time, "end_time": self.end_time, "label": self.label}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Section":
        index = _as_int(data.get("index"), 1)
        return cls(index=index, start_time=str(data.get("start_time", "08:00")), end_time=str(data.get("end_time", "08:45")), label=str(data.get("label", f"第{index}节")))


@dataclass
class Course:
    """One recurring course definition, not one calendar occurrence."""

    id: str = field(default_factory=new_id)
    name: str = "未命名课程"
    weekday: int = 1
    start_section: int = 1
    end_section: int = 1
    start_week: int = 1
    end_week: int = 20
    week_pattern: str = "all"
    custom_weeks: list[int] = field(default_factory=list)
    teacher: str = ""
    building: str = ""
    room: str = ""
    location_text: str = ""
    color: str = "#6C8EF5"
    notes: str = ""
    recognition_status: str = "manual"
    needs_review_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "weekday": self.weekday, "start_section": self.start_section, "end_section": self.end_section, "start_week": self.start_week, "end_week": self.end_week, "week_pattern": self.week_pattern, "custom_weeks": list(self.custom_weeks), "teacher": self.teacher, "building": self.building, "room": self.room, "location_text": self.location_text, "color": self.color, "notes": self.notes, "recognition_status": self.recognition_status, "needs_review_fields": list(self.needs_review_fields)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Course":
        custom_weeks = data.get("custom_weeks", [])
        if not isinstance(custom_weeks, list):
            custom_weeks = []
        needs_review_fields = data.get("needs_review_fields", [])
        if not isinstance(needs_review_fields, list):
            needs_review_fields = []
        return cls(id=str(data.get("id") or new_id()), name=str(data.get("name", "未命名课程")), weekday=_as_int(data.get("weekday"), 1), start_section=_as_int(data.get("start_section"), 1), end_section=_as_int(data.get("end_section"), 1), start_week=_as_int(data.get("start_week"), 1), end_week=_as_int(data.get("end_week"), 20), week_pattern=str(data.get("week_pattern", "all")), custom_weeks=[_as_int(item, 0) for item in custom_weeks], teacher=str(data.get("teacher", "")), building=str(data.get("building", "")), room=str(data.get("room", "")), location_text=str(data.get("location_text", "")), color=str(data.get("color", "#6C8EF5")), notes=str(data.get("notes", "")), recognition_status=str(data.get("recognition_status", "manual")), needs_review_fields=[str(item) for item in needs_review_fields])


@dataclass
class ProjectDocument:
    schema_version: int = SCHEMA_VERSION
    project_name: str = "我的课表"
    school: str = ""
    campus: str = ""
    semester: Semester = field(default_factory=Semester)
    sections: list[Section] = field(default_factory=list)
    courses: list[Course] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @classmethod
    def blank(cls, project_name: str = "我的课表") -> "ProjectDocument":
        default_times = [("08:00", "08:45"), ("08:55", "09:40"), ("10:00", "10:45"), ("10:55", "11:40"), ("14:00", "14:45"), ("14:55", "15:40"), ("16:00", "16:45"), ("16:55", "17:40"), ("19:00", "19:45"), ("19:55", "20:40"), ("20:50", "21:35"), ("21:45", "22:30")]
        sections = [Section(index=i + 1, start_time=start, end_time=end, label=f"第{i + 1}节") for i, (start, end) in enumerate(default_times)]
        return cls(project_name=project_name, sections=sections)

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "project": {"name": self.project_name, "school": self.school, "campus": self.campus, "created_at": self.created_at, "updated_at": self.updated_at}, "semester": self.semester.to_dict(), "sections": [section.to_dict() for section in self.sections], "courses": [course.to_dict() for course in self.courses]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectDocument":
        project = data.get("project") or {}
        if isinstance(project, str):
            project = {"name": project}
        raw_sections = data.get("sections") or []
        raw_courses = data.get("courses") or []
        return cls(schema_version=_as_int(data.get("schema_version"), SCHEMA_VERSION), project_name=str(project.get("name", "我的课表")), school=str(project.get("school", "")), campus=str(project.get("campus", "")), semester=Semester.from_dict(data.get("semester")), sections=[Section.from_dict(item) for item in raw_sections if isinstance(item, dict)], courses=[Course.from_dict(item) for item in raw_courses if isinstance(item, dict)], created_at=str(project.get("created_at", _now_iso())), updated_at=str(project.get("updated_at", _now_iso())))

    def touch(self) -> None:
        self.updated_at = _now_iso()

    def semester_start(self) -> date:
        return date.fromisoformat(self.semester.first_week_monday)
