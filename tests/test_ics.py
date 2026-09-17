from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from scalendar.bridge.app_controller import AppController
from scalendar.core.models import Course, ProjectDocument
from scalendar.exporters.ics import IcsExportError, export_project_to_ics


@pytest.fixture(scope="module")
def qapp():
    app = QCoreApplication.instance() or QCoreApplication([])
    yield app


def make_project() -> ProjectDocument:
    project = ProjectDocument.blank("Apple 日历课表")
    project.school = "南京大学"
    project.campus = "仙林"
    project.semester.name = "2026 秋季学期"
    project.semester.first_week_monday = "2026-09-07"
    project.semester.total_weeks = 16
    project.courses.extend([
        Course(id="all-id", name="高等数学", weekday=1, start_section=1, end_section=2, start_week=1, end_week=16, teacher="李老师", location_text="二教301"),
        Course(id="odd-id", name="大学英语", weekday=3, start_section=3, end_section=4, start_week=1, end_week=16, week_pattern="odd", location_text="一教201"),
        Course(id="even-id", name="物理实验", weekday=4, start_section=5, end_section=6, start_week=2, end_week=16, week_pattern="even", location_text="实验楼"),
        Course(id="custom-id", name="体育", weekday=5, start_section=7, end_section=8, start_week=1, end_week=16, week_pattern="custom", custom_weeks=[1, 4, 8, 12], location_text="体育馆"),
    ])
    return project


def event_blocks(text: str) -> list[str]:
    return [block for block in text.split("BEGIN:VEVENT\r\n")[1:] for block in [block.split("END:VEVENT", 1)[0]]]


def test_ics_expands_all_week_patterns_and_uses_stable_uids(tmp_path: Path):
    path = export_project_to_ics(make_project(), tmp_path / "schedule.ics")
    text = path.read_bytes().decode("utf-8")
    events = event_blocks(text)

    assert text.startswith("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n")
    assert text.endswith("END:VCALENDAR\r\n")
    assert len(events) == 16 + 8 + 8 + 4
    assert "UID:all-id-20260907-1-2@scalendar.local" in text
    assert "DTSTART;TZID=Asia/Shanghai:20260907T080000" in text
    assert "DTEND;TZID=Asia/Shanghai:20260907T094000" in text
    assert "LOCATION:二教301" in text
    assert "X-SCALENDAR-COURSE-ID:all-id" in text
    assert "X-APPLE-STRUCTURED-LOCATION" not in text
    assert "GEO:" not in text


def test_ics_escapes_and_folds_utf8_content_lines(tmp_path: Path):
    project = ProjectDocument.blank("课表")
    project.courses.append(Course(id="special-id", name="实验, A;B", weekday=1, start_section=1, end_section=1, notes="备注" * 50, location_text="教学楼, A;B"))
    path = export_project_to_ics(project, tmp_path / "special.ics")
    text = path.read_bytes().decode("utf-8")
    lines = text.split("\r\n")

    assert "SUMMARY:实验\\, A\\;B" in text
    assert "LOCATION:教学楼\\, A\\;B" in text
    assert "\r\n " in text
    assert all(len(line.encode("utf-8")) <= 75 for line in lines if line)


def test_ics_rejects_invalid_project_and_adds_suffix(tmp_path: Path):
    project = make_project()
    project.sections = []
    with pytest.raises(IcsExportError) as error:
        export_project_to_ics(project, tmp_path / "invalid.ics")
    assert error.value.code == "invalid_project"

    path = export_project_to_ics(make_project(), tmp_path / "without_suffix")
    assert path.name == "without_suffix.ics"


def test_controller_exports_ics_to_selected_location(qapp, tmp_path: Path):
    controller = AppController()
    controller._set_project(make_project(), "")
    target = tmp_path / "calendar.ics"

    assert controller.exportIcs(str(target)) is True
    assert target.exists()
    assert "BEGIN:VEVENT" in target.read_bytes().decode("utf-8")
