from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from scalendar.bridge.app_controller import AppController
from scalendar.bridge.qt_models import CourseListModel, SectionListModel


@pytest.fixture(scope="module")
def qapp():
    app = QCoreApplication.instance() or QCoreApplication([])
    yield app


def make_project(controller: AppController, total_weeks: int = 16) -> None:
    assert controller.createProject("M4 测试课表", "2026 秋季学期", "2026-09-07", total_weeks)


def add_course(controller: AppController, name: str, weekday: int, start: int, end: int) -> str:
    controller.beginNewCourse()
    editor = controller.courseEditor
    editor.name = name
    editor.weekday = weekday
    editor.startSection = start
    editor.endSection = end
    editor.startWeek = 1
    editor.endWeek = 16
    editor.locationText = "原地点"
    assert controller.saveEditor()
    row = controller.courseModel.rowCount() - 1
    return str(controller.courseModel.data(controller.courseModel.index(row, 0), CourseListModel.CourseIdRole))


def names(model) -> list[str]:
    return [str(model.data(model.index(row, 0), CourseListModel.NameRole)) for row in range(model.rowCount())]


def test_course_list_sort_is_view_only_and_uuid_stable(qapp):
    controller = AppController()
    make_project(controller)
    first = add_course(controller, "晚课", 5, 3, 4)
    second = add_course(controller, "早课", 1, 2, 3)
    third = add_course(controller, "中课", 3, 1, 1)

    assert names(controller.courseModel) == ["晚课", "早课", "中课"]
    assert names(controller.courseSortModel) == ["早课", "中课", "晚课"]
    controller.setCourseSort(1)
    assert names(controller.courseSortModel) == ["中课", "早课", "晚课"]
    controller.setCourseSort(2)
    assert names(controller.courseSortModel) == ["中课", "早课", "晚课"]
    assert {first, second, third} == {
        str(controller.courseModel.data(controller.courseModel.index(row, 0), CourseListModel.CourseIdRole))
        for row in range(controller.courseModel.rowCount())
    }


def test_batch_week_location_and_delete_are_atomic(qapp):
    controller = AppController()
    make_project(controller)
    ids = [
        add_course(controller, "课程一", 1, 1, 2),
        add_course(controller, "课程二", 2, 3, 4),
        add_course(controller, "课程三", 3, 5, 6),
    ]

    assert controller.batchUpdateWeeks(ids[:2], 1, 12, "even", "")
    assert controller.batchUpdateLocation(ids[:2], "第二教学楼", "301", "二教301")
    for course_id in ids[:2]:
        course = controller.courseModel.course_at(course_id)
        assert course is not None
        assert course.week_pattern == "even"
        assert course.end_week == 12
        assert course.building == "第二教学楼"
        assert course.room == "301"
        assert course.location_text == "二教301"

    assert controller.batchUpdateWeeks(ids[:2], 1, 12, "custom", "1,1") is False
    assert controller.courseModel.course_at(ids[0]).week_pattern == "even"
    assert controller.batchDeleteCourses(ids[:2])
    assert controller.courseModel.rowCount() == 1
    assert controller.courseModel.course_at(ids[2]) is not None


def test_sections_can_be_added_and_deleted_but_references_are_protected(qapp):
    controller = AppController()
    make_project(controller)
    course_id = add_course(controller, "高等数学", 1, 1, 2)
    assert controller.updateSection(1, "08:00", "08:45")
    assert controller.sectionModel.data(controller.sectionModel.index(0, 0), SectionListModel.WarningRole) == ""
    assert controller.updateSection(2, "08:30", "09:15")
    warning = controller.sectionModel.data(controller.sectionModel.index(0, 0), SectionListModel.WarningRole)
    assert "第 2 节" in warning
    assert controller.updateSection(2, "09:00", "08:45") is False

    original_count = controller.sectionModel.rowCount()
    assert controller.addSection()
    assert controller.sectionModel.rowCount() == original_count + 1
    new_index = max(section.index for section in controller.sectionModel.all_sections())
    assert controller.deleteSection(new_index)
    assert controller.sectionModel.rowCount() == original_count
    errors: list[str] = []
    controller.errorRequested.connect(errors.append)
    assert controller.deleteSection(2) is False
    assert "无法删除第 2 节" in errors[-1]
    assert controller.courseModel.course_at(course_id) is not None


def test_semester_boundary_and_custom_weeks_validation(qapp):
    controller = AppController()
    make_project(controller, 16)
    course_id = add_course(controller, "需要完整学期的课程", 1, 1, 2)
    errors: list[str] = []
    controller.errorRequested.connect(errors.append)

    assert controller.updateSemester("2026 秋季学期", "2026-09-07", 14) is False
    assert controller.totalWeeks == 16
    assert "请先调整课程周次" in errors[-1]

    controller.beginEditCourse(course_id)
    controller.courseEditor.weekPattern = "custom"
    controller.courseEditor.customWeeksText = "1,3,3"
    assert controller.saveEditor() is False
    assert "重复" in errors[-1]
    controller.courseEditor.customWeeksText = "1,3,5"
    assert controller.saveEditor()
    assert controller.courseModel.course_at(course_id).custom_weeks == [1, 3, 5]


def test_m4_save_reload_roundtrip(qapp, tmp_path: Path):
    controller = AppController()
    make_project(controller)
    ids = [add_course(controller, "课程一", 1, 1, 2), add_course(controller, "课程二", 3, 3, 4)]
    assert controller.batchUpdateWeeks(ids, 1, 10, "odd", "")
    assert controller.batchUpdateLocation(ids, "一教", "201", "一教201")
    assert controller.updateSection(1, "07:50", "08:35")
    path = tmp_path / "m4.scalendar"
    assert controller.saveAs(str(path))

    reopened = AppController()
    assert reopened.openProject(str(path))
    assert reopened.totalWeeks == 16
    assert reopened.sectionModel.data(reopened.sectionModel.index(0, 0), SectionListModel.StartTimeRole) == "07:50"
    assert [reopened.courseModel.course_at(course_id).week_pattern for course_id in ids] == ["odd", "odd"]
    assert [reopened.courseModel.course_at(course_id).location_text for course_id in ids] == ["一教201", "一教201"]
