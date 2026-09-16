"""RFC 5545 iCalendar exporter for Apple Calendar and other clients."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from scalendar.core.models import Course, ProjectDocument
from scalendar.core.timetable import iter_course_occurrences
from scalendar.core.validation import validate_project


TIMEZONE_ID = "Asia/Shanghai"
PRODID = "-//Scalendar//Scalendar V1//ZH"


class IcsExportError(ValueError):
    def __init__(self, code: str, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


def export_project_to_ics(project: ProjectDocument, path: str | Path) -> Path:
    """Export one VEVENT per actual class occurrence.

    Expanding occurrences instead of relying on RRULE keeps odd/even/custom
    weeks explicit and gives every event a stable identity derived from the
    Course UUID and occurrence date. Location is deliberately plain text: no
    guessed coordinates or Apple structured-location field is emitted.
    """

    issues = validate_project(project)
    if issues:
        raise IcsExportError("invalid_project", "项目无法导出 ICS：" + "；".join(str(issue) for issue in issues))
    target = Path(path)
    if target.suffix.lower() != ".ics":
        target = target.with_suffix(".ics")
    try:
        payload = _calendar_lines(project)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(("\r\n".join(_fold_line(line) for line in payload) + "\r\n").encode("utf-8"))
    except OSError as exc:
        raise IcsExportError("write_failed", "ICS 文件无法写入，请检查输出位置。", str(exc)) from exc
    return target


def _calendar_lines(project: ProjectDocument) -> list[str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape_text(project.project_name)}",
        f"X-WR-TIMEZONE:{TIMEZONE_ID}",
        "BEGIN:VTIMEZONE",
        f"TZID:{TIMEZONE_ID}",
        f"X-LIC-LOCATION:{TIMEZONE_ID}",
        "BEGIN:STANDARD",
        "DTSTART:19700101T000000",
        "TZOFFSETFROM:+0800",
        "TZOFFSETTO:+0800",
        "TZNAME:CST",
        "END:STANDARD",
        "END:VTIMEZONE",
    ]
    for course in project.courses:
        for occurrence in iter_course_occurrences(project, course):
            lines.extend(_event_lines(project, course, occurrence, stamp))
    lines.append("END:VCALENDAR")
    return lines


def _event_lines(project: ProjectDocument, course: Course, occurrence: object, stamp: str) -> list[str]:
    # CourseOccurrence is intentionally duck-typed here to keep this adapter
    # independent from UI types while retaining the core timetable boundary.
    occurrence_date = occurrence.occurrence_date
    start = _local_datetime(occurrence_date, occurrence.start_time)
    end = _local_datetime(occurrence_date, occurrence.end_time)
    uid = f"{course.id}-{occurrence_date:%Y%m%d}-{course.start_section}-{course.end_section}@scalendar.local"
    location = _location_text(project, course)
    description = _description(course)
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{stamp}",
        f"DTSTART;TZID={TIMEZONE_ID}:{start}",
        f"DTEND;TZID={TIMEZONE_ID}:{end}",
        f"SUMMARY:{_escape_text(course.name)}",
        "STATUS:CONFIRMED",
        "TRANSP:OPAQUE",
        "SEQUENCE:0",
        f"X-SCALENDAR-COURSE-ID:{course.id}",
    ]
    if location:
        lines.append(f"LOCATION:{_escape_text(location)}")
    if description:
        lines.append(f"DESCRIPTION:{_escape_text(description)}")
    lines.extend(["CATEGORIES:课程", "END:VEVENT"])
    return lines


def _local_datetime(occurrence_date: object, value: str) -> str:
    return f"{occurrence_date:%Y%m%d}T{value.replace(':', '')}00"


def _location_text(project: ProjectDocument, course: Course) -> str:
    if course.location_text.strip():
        return course.location_text.strip()
    parts = [project.school, project.campus, course.building, course.room]
    return " ".join(part.strip() for part in parts if part and part.strip())


def _description(course: Course) -> str:
    parts = []
    if course.teacher.strip():
        parts.append(f"教师：{course.teacher.strip()}")
    if course.notes.strip():
        parts.append(f"备注：{course.notes.strip()}")
    return "\n".join(parts)


def _escape_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")


def _fold_line(line: str, limit: int = 75) -> str:
    """Fold an iCalendar content line without splitting UTF-8 characters."""

    raw = line.encode("utf-8")
    if len(raw) <= limit:
        return line
    chunks: list[str] = []
    first = True
    while raw:
        available = limit if first else limit - 1
        end = min(available, len(raw))
        while end > 0 and end < len(raw) and raw[end] & 0xC0 == 0x80:
            end -= 1
        if end <= 0:
            end = min(available, len(raw))
        chunks.append(raw[:end].decode("utf-8"))
        raw = raw[end:]
        first = False
    return "\r\n ".join(chunks)
