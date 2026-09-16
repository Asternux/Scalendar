from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from scalendar.bridge.app_controller import AppController
from scalendar.bridge.qt_models import CourseListModel, SectionListModel


@pytest.fixture(scope="module")
def qapp():
    app = QCoreApplication.instance() or QCoreApplication([])
    yield app


def create_test_project(controller: AppController) -> None:
    assert controller.createProject("我的课表", "2026 秋季学期", "2026-09-07", 20)


def add_course(controller: AppController, name: str = "高等数学") -> str:
    controller.beginNewCourse()
    editor = controller.courseEditor
    editor.name = name
    editor.weekday = 1
    editor.startSection = 1
    editor.endSection = 2
    editor.startWeek = 1
    editor.endWeek = 16
    editor.teacher = "李老师"
    editor.room = "二教301"
    editor.locationText = "二教301"
    assert controller.saveEditor()
    index = controller.courseModel.index(0, 0)
    return str(controller.courseModel.data(index, CourseListModel.CourseIdRole))


def test_create_edit_delete_and_stable_uuid(qapp):
    controller = AppController()
    create_test_project(controller)
    course_id = add_course(controller)

    controller.beginEditCourse(course_id)
    controller.courseEditor.name = "高等数学（已修改）"
    controller.courseEditor.room = "二教302"
    assert controller.saveEditor()

    assert controller.courseModel.rowCount() == 1
    index = controller.courseModel.index(0, 0)
    assert controller.courseModel.data(index, CourseListModel.CourseIdRole) == course_id
    assert controller.courseModel.data(index, CourseListModel.NameRole) == "高等数学（已修改）"
    assert controller.courseModel.data(index, CourseListModel.RoomRole) == "二教302"

    assert controller.deleteCourse(course_id)
    assert controller.courseModel.rowCount() == 0


def test_course_model_exposes_typed_roles(qapp):
    controller = AppController()
    role_names = set(controller.courseModel.roleNames().values())
    expected = {
        b"courseId", b"name", b"weekday", b"startSection", b"endSection",
        b"startWeek", b"endWeek", b"weekPattern", b"customWeeks", b"teacher",
        b"building", b"room", b"locationText", b"color", b"notes",
        b"recognitionStatus",
    }
    assert expected <= role_names


def test_save_autosave_reload_and_section_edit(qapp, tmp_path: Path):
    controller = AppController()
    create_test_project(controller)
    course_id = add_course(controller, "大学英语")
    project_path = tmp_path / "fall.scalendar"

    assert controller.saveAs(str(project_path))
    assert controller.dirty is False
    assert controller.updateSection(1, "07:50", "08:35")
    assert controller.dirty is True

    controller.beginEditCourse(course_id)
    controller.courseEditor.name = "大学英语（改名）"
    controller.courseEditor.weekday = 4
    controller.courseEditor.room = "一教202"
    assert controller.saveEditor()
    controller.flushAutosave()
    assert controller.dirty is False

    reopened = AppController()
    assert reopened.openProject(str(project_path))
    assert reopened.projectName == "我的课表"
    assert reopened.courseModel.rowCount() == 1
    course_index = reopened.courseModel.index(0, 0)
    assert reopened.courseModel.data(course_index, CourseListModel.CourseIdRole) == course_id
    assert reopened.courseModel.data(course_index, CourseListModel.NameRole) == "大学英语（改名）"
    assert reopened.courseModel.data(course_index, CourseListModel.WeekdayRole) == 4
    assert reopened.courseModel.data(course_index, CourseListModel.RoomRole) == "一教202"
    section_index = reopened.sectionModel.index(0, 0)
    assert reopened.sectionModel.data(section_index, SectionListModel.StartTimeRole) == "07:50"
    assert reopened.sectionModel.data(section_index, SectionListModel.EndTimeRole) == "08:35"


def test_invalid_project_is_reported_without_crashing(qapp, tmp_path: Path):
    invalid_path = tmp_path / "invalid.scalendar"
    invalid_path.write_text(
        '{"schema_version": 1, "project": {"name": "坏项目"}, '
        '"semester": {"first_week_monday": "2026-09-08", "total_weeks": 20}, '
        '"sections": [], "courses": []}',
        encoding="utf-8",
    )
    controller = AppController()
    errors: list[str] = []
    controller.errorRequested.connect(errors.append)

    assert controller.openProject(str(invalid_path)) is False
    assert errors
    assert "周一" in errors[-1]


def test_three_course_acceptance_flow_survives_reopen(qapp, tmp_path: Path):
    controller = AppController()
    create_test_project(controller)
    rows = [
        ("高等数学", 1, 1, 2, "二教301", "all"),
        ("大学英语", 3, 3, 4, "一教201", "all"),
        ("体育", 5, 5, 6, "体育馆", "even"),
    ]
    ids = []
    for name, weekday, start, end, location, pattern in rows:
        controller.beginNewCourse()
        editor = controller.courseEditor
        editor.name = name
        editor.weekday = weekday
        editor.startSection = start
        editor.endSection = end
        editor.startWeek = 1
        editor.endWeek = 16
        editor.weekPattern = pattern
        editor.locationText = location
        assert controller.saveEditor()
        ids.append(controller.courseModel.data(controller.courseModel.index(len(ids), 0), CourseListModel.CourseIdRole))

    path = tmp_path / "acceptance.scalendar"
    assert controller.saveAs(str(path))
    controller.beginEditCourse(ids[0])
    controller.courseEditor.weekday = 2
    controller.courseEditor.room = "二教302"
    assert controller.saveEditor()
    controller.flushAutosave()

    reopened = AppController()
    assert reopened.openProject(str(path))
    assert reopened.courseModel.rowCount() == 3
    reopened_ids = [reopened.courseModel.data(reopened.courseModel.index(row, 0), CourseListModel.CourseIdRole) for row in range(3)]
    assert reopened_ids == ids
    moved = reopened.courseModel.index(0, 0)
    assert reopened.courseModel.data(moved, CourseListModel.WeekdayRole) == 2
    assert reopened.courseModel.data(moved, CourseListModel.RoomRole) == "二教302"
    sports = reopened.courseModel.index(2, 0)
    assert reopened.courseModel.data(sports, CourseListModel.WeekPatternRole) == "even"
