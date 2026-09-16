from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from scalendar.bridge.app_controller import AppController
from scalendar.core.models import Course, ProjectDocument
from scalendar.importers.xlsx import ExcelImportError, import_xlsx
from scalendar.exporters.xlsx import COURSE_HEADERS, export_project_to_xlsx
from scalendar.excel.xlsx_io import XlsxReader, XlsxWriter
from scalendar.recognition.normalizer import candidate_to_course


@pytest.fixture(scope="module")
def qapp():
    app = QCoreApplication.instance() or QCoreApplication([])
    yield app


def make_project() -> ProjectDocument:
    project = ProjectDocument.blank("2026 秋季学期课表")
    project.school = "南京大学"
    project.campus = "仙林"
    project.semester.name = "2026 秋季学期"
    project.semester.first_week_monday = "2026-09-07"
    project.semester.total_weeks = 16
    project.courses.extend([
        Course(id="all-id", name="高等数学", weekday=1, start_section=1, end_section=2, start_week=1, end_week=16, week_pattern="all", teacher="李老师", building="二教", room="301", location_text="二教301", notes="必修"),
        Course(id="odd-id", name="大学英语", weekday=3, start_section=3, end_section=4, start_week=1, end_week=16, week_pattern="odd", teacher="王老师", building="一教", room="201", location_text="一教201"),
        Course(id="even-id", name="物理实验", weekday=4, start_section=5, end_section=6, start_week=2, end_week=16, week_pattern="even", teacher="赵老师", location_text="实验楼"),
        Course(id="custom-id", name="体育", weekday=5, start_section=7, end_section=8, start_week=1, end_week=16, week_pattern="custom", custom_weeks=[1, 4, 8, 12], teacher="张老师", location_text="体育馆"),
    ])
    return project


def standard_rows(course_rows=None):
    rows = [
        ["设置", "值"],
        ["格式版本", "Scalendar XLSX 1"],
        ["项目名称", "导入项目"],
        ["学期名称", "2026 秋季学期"],
        ["第一教学周周一", "2026-09-07"],
        ["总周数", 16],
        ["学校", "南京大学"],
        ["校区", "仙林"],
        [],
        ["节次", "开始时间", "结束时间", "标签"],
        *[[index, start, end, f"第{index}节"] for index, (start, end) in enumerate([
            ("08:00", "08:45"), ("08:55", "09:40"), ("10:00", "10:45"), ("10:55", "11:40"),
            ("14:00", "14:45"), ("14:55", "15:40"), ("16:00", "16:45"), ("16:55", "17:40"),
            ("19:00", "19:45"), ("19:55", "20:40"), ("20:50", "21:35"), ("21:45", "22:30"),
        ], start=1)],
    ]
    courses = [COURSE_HEADERS]
    courses.extend(course_rows or [["高等数学", "周一", 1, 2, 1, 16, "每周", "", "南京大学", "仙林", "二教", "301", "二教301", "李老师", ""]])
    return rows, courses


def write_standard(path: Path, course_rows=None, *, only: str | None = None) -> None:
    settings, courses = standard_rows(course_rows)
    writer = XlsxWriter()
    if only != "Settings":
        writer.add_sheet("Courses", courses, widths=[20] * len(COURSE_HEADERS), autofilter=True)
    if only != "Courses":
        writer.add_sheet("Settings", settings, widths=[20, 20, 20, 20], header_rows=(1, 10))
    writer.save(path)


def test_export_creates_standard_sheets_headers_and_readable_settings(tmp_path: Path):
    path = export_project_to_xlsx(make_project(), tmp_path / "schedule.xlsx")
    reader = XlsxReader(path)
    assert reader.sheet_names == ["Courses", "Settings"]
    assert reader.rows("Courses")[0] == COURSE_HEADERS
    settings = {str(row[0]): row[1] for row in reader.rows("Settings") if len(row) >= 2 and row[0]}
    assert settings["学期名称"] == "2026 秋季学期"
    assert settings["第一教学周周一"] == "2026-09-07"
    assert settings["总周数"] == 16
    assert settings["学校"] == "南京大学"


def test_standard_xlsx_roundtrip_preserves_course_information_but_generates_new_ids(tmp_path: Path):
    original = make_project()
    result = import_xlsx(export_project_to_xlsx(original, tmp_path / "roundtrip.xlsx"))
    assert result.workbook_kind == "standard"
    assert len(result.candidates) == 4
    assert [course.week_pattern for course in result.candidates] == ["all", "odd", "even", "custom"]
    assert result.candidates[3].custom_weeks == [1, 4, 8, 12]
    imported = ProjectDocument.blank(result.project_name)
    imported.semester.name = result.semester_name
    imported.semester.first_week_monday = result.first_week_monday
    imported.semester.total_weeks = result.total_weeks
    imported.school, imported.campus = result.school, result.campus
    imported.sections = result.sections
    imported.courses = [candidate_to_course(candidate, imported.semester.total_weeks, tuple(section.index for section in imported.sections)) for candidate in result.candidates]
    assert [course.name for course in imported.courses] == [course.name for course in original.courses]
    assert [course.location_text for course in imported.courses] == [course.location_text for course in original.courses]
    assert [course.teacher for course in imported.courses] == [course.teacher for course in original.courses]
    assert [course.id for course in imported.courses] != [course.id for course in original.courses]


def test_export_does_not_include_internal_ids_or_recognition_private_fields(tmp_path: Path):
    project = make_project()
    project.courses[0].recognition_status = "needs_review"
    project.courses[0].needs_review_fields = ["weekday"]
    path = export_project_to_xlsx(project, tmp_path / "public.xlsx")
    raw = path.read_bytes()
    assert b"all-id" not in raw
    assert b"needs_review" not in raw
    assert b"recognition_status" not in raw
    assert b"OPENAI_API_KEY" not in raw


def test_import_rejects_missing_sheets_and_columns(tmp_path: Path):
    missing_courses = tmp_path / "missing-courses.xlsx"
    write_standard(missing_courses, only="Settings")
    with pytest.raises(ExcelImportError) as missing:
        import_xlsx(missing_courses)
    assert missing.value.code == "missing_courses"

    missing_columns = tmp_path / "missing-columns.xlsx"
    settings, _ = standard_rows()
    writer = XlsxWriter()
    writer.add_sheet("Courses", [["课程名称"], ["高等数学"]])
    writer.add_sheet("Settings", settings, header_rows=(1, 10))
    writer.save(missing_columns)
    with pytest.raises(ExcelImportError) as columns:
        import_xlsx(missing_columns)
    assert columns.value.code == "missing_columns"


def test_import_rejects_invalid_cell_and_ranges(tmp_path: Path):
    cases = [
        (["课程", "星期八", 1, 2, 1, 16, "每周", "", "", "", "", "", "", "", ""], "invalid_cell"),
        (["课程", "周一", 99, 2, 1, 16, "每周", "", "", "", "", "", "", "", ""], "out_of_range"),
        (["课程", "周一", 1, 2, 0, 16, "每周", "", "", "", "", "", "", "", ""], "out_of_range"),
        (["课程", "周一", 1, 2, 1, 16, "自定义", "", "", "", "", "", "", "", ""], "invalid_cell"),
    ]
    for index, (row, expected_code) in enumerate(cases):
        path = tmp_path / f"invalid-{index}.xlsx"
        write_standard(path, [row])
        with pytest.raises(ExcelImportError) as error:
            import_xlsx(path)
        assert error.value.code == expected_code


def test_import_rejects_corrupt_xlsx_and_wrong_extension(tmp_path: Path):
    wrong = tmp_path / "schedule.xls"
    wrong.write_text("not xlsx", encoding="utf-8")
    with pytest.raises(ExcelImportError) as wrong_error:
        import_xlsx(wrong)
    assert wrong_error.value.code == "not_xlsx"

    corrupt = tmp_path / "broken.xlsx"
    corrupt.write_bytes(b"not a zip")
    with pytest.raises(ExcelImportError) as corrupt_error:
        import_xlsx(corrupt)
    assert corrupt_error.value.code == "file_corrupt"


def test_external_excel_is_conservative_and_marks_missing_fields(tmp_path: Path):
    path = tmp_path / "external.xlsx"
    writer = XlsxWriter()
    writer.add_sheet("课程表", [["课程", "星期", "开始节次", "结束节次", "地点", "教师"], ["高等数学", "周一", 1, 2, "二教301", "李老师"]])
    writer.save(path)
    result = import_xlsx(path)
    assert result.workbook_kind == "external"
    assert result.candidates[0].name == "高等数学"
    assert set(result.candidates[0].needs_review_fields) >= {"start_week", "end_week", "week_pattern"}

    unknown = tmp_path / "unknown.xlsx"
    writer = XlsxWriter()
    writer.add_sheet("Sheet1", [["说明", "内容"], ["随机表", "无法理解"]])
    writer.save(unknown)
    with pytest.raises(ExcelImportError) as error:
        import_xlsx(unknown)
    assert error.value.code == "unrecognized_structure"


def test_controller_exports_and_appends_excel_import(qapp, tmp_path: Path):
    source = make_project()
    source_path = export_project_to_xlsx(source, tmp_path / "source.xlsx")
    controller = AppController()
    assert controller.createProject("空白项目", "临时学期", "2026-09-07", 20)
    assert controller.selectExcel(str(source_path))
    assert controller.excelState == "ready_to_import"
    assert controller.excelSheetCount == 2
    assert controller.excelCourseCount == 4
    assert controller.applyExcelImport()
    assert controller.courseModel.rowCount() == 4
    assert controller.projectName == "2026 秋季学期课表"
    assert controller.school == "南京大学"
    assert controller.totalWeeks == 16

    export_path = tmp_path / "controller-output.xlsx"
    assert controller.exportExcel(str(export_path))
    assert export_path.exists()


def test_controller_reports_excel_error_without_crashing(qapp, tmp_path: Path):
    bad = tmp_path / "bad.xlsx"
    bad.write_bytes(b"bad")
    controller = AppController()
    errors: list[str] = []
    controller.errorRequested.connect(errors.append)
    assert controller.selectExcel(str(bad)) is False
    assert controller.excelState == "error"
    assert errors
    assert "Excel" in errors[-1]
