"""Conservative Scalendar and external XLSX importer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from scalendar.core.models import Section
from scalendar.core.validation import parse_custom_weeks
from scalendar.excel.xlsx_io import XlsxError, XlsxReader
from scalendar.recognition.models import CandidateCourse

from scalendar.exporters.xlsx import COURSE_HEADERS, PATTERN_NAMES, WEEKDAY_NAMES


class ExcelImportError(ValueError):
    def __init__(self, code: str, message: str, detail: str = "", row: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail
        self.row = row


@dataclass
class ExcelImportResult:
    candidates: list[CandidateCourse] = field(default_factory=list)
    project_name: str = "导入课表"
    semester_name: str = "未命名学期"
    first_week_monday: str = "2026-09-07"
    total_weeks: int = 20
    school: str = ""
    campus: str = ""
    sections: list[Section] = field(default_factory=list)
    workbook_kind: str = "standard"
    sheet_names: list[str] = field(default_factory=list)
    format_text: str = ""
    issues: list[str] = field(default_factory=list)


_WEEKDAY_ALIASES = {name: index for index, name in enumerate(WEEKDAY_NAMES, start=1)}
_WEEKDAY_ALIASES.update({f"星期{index}": index for index in range(1, 7)})
_WEEKDAY_ALIASES.update({"星期日": 7, "星期天": 7, "周天": 7})
_PATTERN_ALIASES = {value: key for key, value in PATTERN_NAMES.items()}
_PATTERN_ALIASES.update({"all": "all", "odd": "odd", "even": "even", "custom": "custom"})


def import_xlsx(path: str | Path) -> ExcelImportResult:
    source = Path(path)
    if source.suffix.lower() != ".xlsx":
        raise ExcelImportError("not_xlsx", "请选择 XLSX 文件。")
    try:
        workbook = XlsxReader(source)
    except XlsxError as exc:
        raise ExcelImportError(exc.code, exc.message, exc.detail) from exc
    names = workbook.sheet_names
    if "Courses" in names or "Settings" in names:
        if "Courses" not in names:
            raise ExcelImportError("missing_courses", "缺少必要 Sheet：Courses。")
        if "Settings" not in names:
            raise ExcelImportError("missing_settings", "缺少必要 Sheet：Settings。")
        return _parse_standard(workbook, names)
    return _parse_external(workbook, names)


def _parse_standard(workbook: XlsxReader, names: list[str]) -> ExcelImportResult:
    result = _parse_settings(workbook.rows("Settings"), names)
    rows = workbook.rows("Courses")
    if not rows:
        raise ExcelImportError("missing_columns", "Courses Sheet 缺少表头。")
    headers = [_text(value) for value in rows[0]]
    missing = [header for header in COURSE_HEADERS if header not in headers]
    if missing:
        raise ExcelImportError("missing_columns", "Courses Sheet 缺少必要列：" + "、".join(missing))
    columns = {header: headers.index(header) for header in COURSE_HEADERS}
    section_indices = tuple(section.index for section in result.sections) or tuple(range(1, 13))
    for row_number, row in enumerate(rows[1:], start=2):
        if not any(_text(value).strip() for value in row):
            continue
        result.candidates.append(_parse_standard_course(row, columns, result, section_indices, row_number))
    if not result.candidates:
        raise ExcelImportError("no_courses", "Courses Sheet 没有可导入的课程。")
    result.workbook_kind = "standard"
    result.format_text = "检测到 Scalendar 标准工作簿"
    return result


def _parse_settings(rows: list[list[Any]], names: list[str]) -> ExcelImportResult:
    values: dict[str, Any] = {}
    section_header = -1
    for index, row in enumerate(rows):
        key = _text(row[0]) if row else ""
        if key == "节次" and len(row) >= 3 and _text(row[1]) == "开始时间":
            section_header = index
            continue
        if len(row) >= 2 and key:
            values[key] = row[1]
    total_weeks = _required_int(values.get("总周数"), "总周数")
    if not 1 <= total_weeks <= 60:
        raise ExcelImportError("out_of_range", "总周数必须在 1 到 60 周之间。")
    first_monday = _text(values.get("第一教学周周一"))
    try:
        monday = date.fromisoformat(first_monday)
    except ValueError as exc:
        raise ExcelImportError("invalid_settings", "第一教学周周一必须是 YYYY-MM-DD 日期。") from exc
    if monday.weekday() != 0:
        raise ExcelImportError("invalid_settings", "第一教学周周一必须是周一。")
    sections: list[Section] = []
    if section_header >= 0:
        for row_number, row in enumerate(rows[section_header + 1 :], start=section_header + 2):
            if not any(_text(value).strip() for value in row):
                continue
            if len(row) < 3:
                raise ExcelImportError("invalid_cell", f"Settings 第 {row_number} 行节次数据不完整。", row=row_number)
            index = _required_int(row[0], "节次", row_number)
            start, end = _text(row[1]), _text(row[2])
            if not _valid_time(start) or not _valid_time(end) or start >= end:
                raise ExcelImportError("invalid_cell", f"Settings 第 {row_number} 行节次时间无效。", row=row_number)
            sections.append(Section(index=index, start_time=start, end_time=end, label=_text(row[3]) if len(row) > 3 else f"第{index}节"))
    return ExcelImportResult(
        project_name=_text(values.get("项目名称")) or "导入课表",
        semester_name=_text(values.get("学期名称")) or "未命名学期",
        first_week_monday=first_monday,
        total_weeks=total_weeks,
        school=_text(values.get("学校")),
        campus=_text(values.get("校区")),
        sections=sections,
        sheet_names=names,
    )


def _parse_standard_course(row: list[Any], columns: dict[str, int], result: ExcelImportResult, section_indices: tuple[int, ...], row_number: int) -> CandidateCourse:
    def value(header: str) -> Any:
        index = columns[header]
        return row[index] if index < len(row) else None

    name = _text(value("课程名称")).strip()
    if not name:
        raise ExcelImportError("invalid_cell", f"Courses 第 {row_number} 行课程名称不能为空。", row=row_number)
    weekday = _parse_weekday(value("星期"), row_number)
    start_section = _required_int(value("开始节次"), "开始节次", row_number)
    end_section = _required_int(value("结束节次"), "结束节次", row_number)
    start_week = _required_int(value("开始周"), "开始周", row_number)
    end_week = _required_int(value("结束周"), "结束周", row_number)
    pattern = _parse_pattern(value("周期"), row_number)
    custom_text = _text(value("指定周"))
    _validate_course_range(weekday, start_section, end_section, start_week, end_week, pattern, custom_text, result.total_weeks, section_indices, row_number)
    custom_weeks = parse_custom_weeks(custom_text, result.total_weeks, required=pattern == "custom")
    return CandidateCourse(
        name=name,
        weekday=weekday,
        start_section=start_section,
        end_section=end_section,
        start_week=start_week,
        end_week=end_week,
        week_pattern=pattern,
        custom_weeks=custom_weeks,
        teacher=_text(value("教师")).strip(),
        building=_text(value("教学楼")).strip(),
        room=_text(value("教室")).strip(),
        location_text=_text(value("地点")).strip(),
        notes=_text(value("备注")).strip(),
    )


def _parse_external(workbook: XlsxReader, names: list[str]) -> ExcelImportResult:
    aliases = {
        "name": {"课程名称", "课程", "课程名", "科目", "课名"},
        "weekday": {"星期", "上课星期", "周几"},
        "start_section": {"开始节次", "起始节次", "开始节", "节次"},
        "end_section": {"结束节次", "终止节次", "结束节"},
        "start_week": {"开始周", "起始周", "周次开始"},
        "end_week": {"结束周", "终止周", "周次结束"},
        "pattern": {"周期", "单双周", "周次类型"},
        "custom_weeks": {"指定周", "自定义周次"},
        "teacher": {"教师", "老师", "任课教师"},
        "building": {"教学楼", "楼栋"},
        "room": {"教室", "上课地点"},
        "location": {"地点", "上课地点", "教室"},
        "notes": {"备注", "说明"},
    }
    for sheet_name in names:
        rows = workbook.rows(sheet_name)
        if not rows:
            continue
        headers = [_text(value).strip() for value in rows[0]]
        mapping = {}
        for field_name, candidates in aliases.items():
            for index, header in enumerate(headers):
                if header in candidates:
                    mapping[field_name] = index
                    break
        if not {"name", "weekday", "start_section", "end_section"} <= set(mapping):
            continue
        result = ExcelImportResult(
            workbook_kind="external",
            sheet_names=names,
            format_text="检测到外部课表，已生成候选课程",
            total_weeks=20,
        )
        for row_number, row in enumerate(rows[1:], start=2):
            get = lambda key: row[mapping[key]] if key in mapping and mapping[key] < len(row) else None
            name = _text(get("name")).strip()
            if not name:
                continue
            review: set[str] = set()
            weekday = _optional_weekday(get("weekday"), review, "weekday")
            start_section = _optional_int(get("start_section"), review, "start_section")
            end_section = _optional_int(get("end_section"), review, "end_section")
            start_week = _optional_int(get("start_week"), review, "start_week")
            end_week = _optional_int(get("end_week"), review, "end_week")
            if start_week is None:
                review.add("start_week")
            if end_week is None:
                review.add("end_week")
            pattern_text = _text(get("pattern")) if "pattern" in mapping else ""
            pattern = _PATTERN_ALIASES.get(pattern_text.strip(), "all")
            if not pattern_text:
                review.add("week_pattern")
            custom_text = _text(get("custom_weeks")) if "custom_weeks" in mapping else ""
            custom_weeks: list[int] = []
            if pattern == "custom":
                try:
                    custom_weeks = parse_custom_weeks(custom_text, result.total_weeks, required=True)
                except ValueError:
                    review.add("custom_weeks")
            result.candidates.append(CandidateCourse(
                name=name,
                weekday=weekday,
                start_section=start_section,
                end_section=end_section,
                start_week=start_week,
                end_week=end_week,
                week_pattern=pattern,
                custom_weeks=custom_weeks,
                teacher=_text(get("teacher")).strip(),
                building=_text(get("building")).strip(),
                room=_text(get("room")).strip(),
                location_text=_text(get("location")).strip(),
                notes=_text(get("notes")).strip(),
                needs_review_fields=sorted(review),
            ))
        if result.candidates:
            return result
    raise ExcelImportError("unrecognized_structure", "无法可靠识别该 Excel 的课表结构。")


def _validate_course_range(weekday: int, start_section: int, end_section: int, start_week: int, end_week: int, pattern: str, custom_text: str, total_weeks: int, section_indices: tuple[int, ...], row_number: int) -> None:
    valid_sections = set(section_indices)
    if not 1 <= weekday <= 7:
        raise ExcelImportError("out_of_range", f"Courses 第 {row_number} 行星期超出范围。", row=row_number)
    if start_section > end_section or start_section not in valid_sections or end_section not in valid_sections or any(item not in valid_sections for item in range(start_section, end_section + 1)):
        raise ExcelImportError("out_of_range", f"Courses 第 {row_number} 行节次超出项目设置。", row=row_number)
    if not 1 <= start_week <= end_week <= total_weeks:
        raise ExcelImportError("out_of_range", f"Courses 第 {row_number} 行周次超出学期范围。", row=row_number)
    if pattern == "custom":
        try:
            parse_custom_weeks(custom_text, total_weeks, required=True)
        except ValueError as exc:
            raise ExcelImportError("invalid_cell", f"Courses 第 {row_number} 行指定周无效：{exc}", row=row_number) from exc


def _parse_weekday(value: Any, row_number: int) -> int:
    text = _text(value).strip()
    if text in _WEEKDAY_ALIASES:
        return _WEEKDAY_ALIASES[text]
    number = _optional_int_value(value)
    if number is not None:
        return number
    raise ExcelImportError("invalid_cell", f"Courses 第 {row_number} 行星期格式错误。", row=row_number)


def _parse_pattern(value: Any, row_number: int) -> str:
    pattern = _PATTERN_ALIASES.get(_text(value).strip())
    if pattern is None:
        raise ExcelImportError("invalid_cell", f"Courses 第 {row_number} 行周期必须是每周、单周、双周或自定义。", row=row_number)
    return pattern


def _required_int(value: Any, field_name: str, row_number: int | None = None) -> int:
    parsed = _optional_int_value(value)
    if parsed is None:
        suffix = f"第 {row_number} 行" if row_number else ""
        raise ExcelImportError("invalid_cell", f"{suffix}{field_name}必须是整数。", row=row_number)
    return parsed


def _optional_int(value: Any, review: set[str], field_name: str) -> int | None:
    parsed = _optional_int_value(value)
    if parsed is None and _text(value).strip():
        review.add(field_name)
    return parsed


def _optional_weekday(value: Any, review: set[str], field_name: str) -> int | None:
    text = _text(value).strip()
    if text in _WEEKDAY_ALIASES:
        return _WEEKDAY_ALIASES[text]
    parsed = _optional_int_value(value)
    if parsed is None or not 1 <= parsed <= 7:
        review.add(field_name)
        return None
    return parsed


def _optional_int_value(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    text = _text(value).strip()
    if text.isdigit():
        return int(text)
    return None


def _valid_time(value: str) -> bool:
    if len(value) != 5 or value[2] != ":":
        return False
    try:
        hour, minute = int(value[:2]), int(value[3:])
    except ValueError:
        return False
    return 0 <= hour <= 23 and 0 <= minute <= 59


def _text(value: Any) -> str:
    return "" if value is None else str(value)
