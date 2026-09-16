"""Qt list models used by the QML editor.

The QML layer receives role-based values from these models rather than a
collection of Python dictionaries. The core dataclasses remain independent of
Qt and are still the source of truth.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Slot, QObject, Property, QSortFilterProxyModel, Signal

from scalendar.core.models import Course, ProjectDocument, Section
from scalendar.core.timetable_layout import DEFAULT_TIMETABLE_LAYOUT
from scalendar.recognition.models import CandidateCourse


class TimetableLayoutModel(QObject):
    """Expose one source of timetable geometry tokens to QML."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._spec = DEFAULT_TIMETABLE_LAYOUT

    @Property(int, constant=True)
    def timeColumnWidth(self) -> int:
        return self._spec.time_column_width

    @Property(int, constant=True)
    def dayHeaderHeight(self) -> int:
        return self._spec.day_header_height

    @Property(int, constant=True)
    def sectionHeight(self) -> int:
        return self._spec.section_height

    @Property(int, constant=True)
    def cellGap(self) -> int:
        return self._spec.cell_gap


class CourseListModel(QAbstractListModel):
    countChanged = Signal()
    CourseIdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    WeekdayRole = Qt.UserRole + 3
    StartSectionRole = Qt.UserRole + 4
    EndSectionRole = Qt.UserRole + 5
    StartWeekRole = Qt.UserRole + 6
    EndWeekRole = Qt.UserRole + 7
    WeekPatternRole = Qt.UserRole + 8
    CustomWeeksRole = Qt.UserRole + 9
    TeacherRole = Qt.UserRole + 10
    BuildingRole = Qt.UserRole + 11
    RoomRole = Qt.UserRole + 12
    LocationTextRole = Qt.UserRole + 13
    ColorRole = Qt.UserRole + 14
    NotesRole = Qt.UserRole + 15
    RecognitionStatusRole = Qt.UserRole + 16
    CourseColorRole = Qt.UserRole + 17
    NeedsReviewFieldsRole = Qt.UserRole + 18

    _roles = {
        CourseIdRole: b"courseId",
        NameRole: b"name",
        WeekdayRole: b"weekday",
        StartSectionRole: b"startSection",
        EndSectionRole: b"endSection",
        StartWeekRole: b"startWeek",
        EndWeekRole: b"endWeek",
        WeekPatternRole: b"weekPattern",
        CustomWeeksRole: b"customWeeks",
        TeacherRole: b"teacher",
        BuildingRole: b"building",
        RoomRole: b"room",
        LocationTextRole: b"locationText",
        ColorRole: b"color",
        NotesRole: b"notes",
        RecognitionStatusRole: b"recognitionStatus",
        CourseColorRole: b"courseColor",
        NeedsReviewFieldsRole: b"needsReviewFields",
    }

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._courses: list[Course] = []

    def roleNames(self) -> dict[int, bytes]:
        return self._roles

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._courses)

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._courses)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._courses):
            return None
        course = self._courses[index.row()]
        values = {
            self.CourseIdRole: course.id,
            self.NameRole: course.name,
            self.WeekdayRole: course.weekday,
            self.StartSectionRole: course.start_section,
            self.EndSectionRole: course.end_section,
            self.StartWeekRole: course.start_week,
            self.EndWeekRole: course.end_week,
            self.WeekPatternRole: course.week_pattern,
            self.CustomWeeksRole: list(course.custom_weeks),
            self.TeacherRole: course.teacher,
            self.BuildingRole: course.building,
            self.RoomRole: course.room,
            self.LocationTextRole: course.location_text,
            self.ColorRole: course.color,
            self.NotesRole: course.notes,
            self.RecognitionStatusRole: course.recognition_status,
            self.CourseColorRole: course.color,
            self.NeedsReviewFieldsRole: list(course.needs_review_fields),
        }
        return values.get(role)

    def refresh(self, courses: list[Course]) -> None:
        self.beginResetModel()
        self._courses = list(courses)
        self.endResetModel()
        self.countChanged.emit()

    def append_course(self, course: Course) -> None:
        row = len(self._courses)
        self.beginInsertRows(QModelIndex(), row, row)
        self._courses.append(course)
        self.endInsertRows()
        self.countChanged.emit()

    def update_course(self, course: Course) -> bool:
        for row, current in enumerate(self._courses):
            if current.id == course.id:
                self._courses[row] = course
                index = self.index(row, 0)
                self.dataChanged.emit(index, index, list(self._roles))
                return True
        return False

    def remove_course(self, course_id: str) -> bool:
        for row, course in enumerate(self._courses):
            if course.id == course_id:
                self.beginRemoveRows(QModelIndex(), row, row)
                self._courses.pop(row)
                self.endRemoveRows()
                self.countChanged.emit()
                return True
        return False

    def course_at(self, course_id: str) -> Course | None:
        return next((course for course in self._courses if course.id == course_id), None)

    def all_courses(self) -> list[Course]:
        return list(self._courses)


class CourseSortProxyModel(QSortFilterProxyModel):
    """A view-only sort over the shared course model.

    The source model remains the project's canonical course order. Sorting
    therefore cannot mutate persisted order or affect stable course IDs.
    """

    sortModeChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._sort_mode = 0
        self.setDynamicSortFilter(True)
        self.sort(0, Qt.AscendingOrder)

    @Property(int, notify=sortModeChanged)
    def sortMode(self) -> int:
        return self._sort_mode

    @Slot(int)
    def setSortMode(self, mode: int) -> None:
        mode = max(0, min(2, int(mode)))
        if self._sort_mode == mode:
            self.sort(0, Qt.AscendingOrder)
            return
        self._sort_mode = mode
        self.sortModeChanged.emit()
        self.invalidate()
        self.sort(0, Qt.AscendingOrder)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        source = self.sourceModel()
        if source is None:
            return False
        role = CourseListModel
        left_name = str(source.data(left, role.NameRole) or "").casefold()
        right_name = str(source.data(right, role.NameRole) or "").casefold()
        left_weekday = int(source.data(left, role.WeekdayRole) or 0)
        right_weekday = int(source.data(right, role.WeekdayRole) or 0)
        left_start = int(source.data(left, role.StartSectionRole) or 0)
        right_start = int(source.data(right, role.StartSectionRole) or 0)
        if self._sort_mode == 1:
            return (left_name, left_weekday, left_start) < (right_name, right_weekday, right_start)
        if self._sort_mode == 2:
            return (left_start, left_weekday, left_name) < (right_start, right_weekday, right_name)
        return (left_weekday, left_start, left_name) < (right_weekday, right_start, right_name)


class SectionListModel(QAbstractListModel):
    countChanged = Signal()
    IndexRole = Qt.UserRole + 1
    StartTimeRole = Qt.UserRole + 2
    EndTimeRole = Qt.UserRole + 3
    LabelRole = Qt.UserRole + 4
    WarningRole = Qt.UserRole + 5

    _roles = {
        IndexRole: b"sectionIndex",
        StartTimeRole: b"startTime",
        EndTimeRole: b"endTime",
        LabelRole: b"label",
        WarningRole: b"warningText",
    }

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._sections: list[Section] = []
        self._warnings: list[str] = []

    def roleNames(self) -> dict[int, bytes]:
        return self._roles

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._sections)

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._sections)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._sections):
            return None
        section = self._sections[index.row()]
        return {
            self.IndexRole: section.index,
            self.StartTimeRole: section.start_time,
            self.EndTimeRole: section.end_time,
            self.LabelRole: section.label,
            self.WarningRole: self._warnings[index.row()] if index.row() < len(self._warnings) else "",
        }.get(role)

    def _recompute_warnings(self) -> None:
        warnings = ["" for _ in self._sections]
        for left_row, left in enumerate(self._sections):
            for right_row in range(left_row + 1, len(self._sections)):
                right = self._sections[right_row]
                if left.start_time < right.end_time and right.start_time < left.end_time:
                    warnings[left_row] = f"与第 {right.index} 节时间重叠"
                    warnings[right_row] = f"与第 {left.index} 节时间重叠"
        self._warnings = warnings

    def refresh(self, sections: list[Section]) -> None:
        self.beginResetModel()
        self._sections = list(sections)
        self._recompute_warnings()
        self.endResetModel()
        self.countChanged.emit()

    def append_section(self, section: Section) -> None:
        row = len(self._sections)
        self.beginInsertRows(QModelIndex(), row, row)
        self._sections.append(section)
        self._recompute_warnings()
        self.endInsertRows()
        self.countChanged.emit()

    def remove_section(self, section_index: int) -> bool:
        for row, section in enumerate(self._sections):
            if section.index == section_index:
                self.beginRemoveRows(QModelIndex(), row, row)
                self._sections.pop(row)
                self._recompute_warnings()
                self.endRemoveRows()
                self.countChanged.emit()
                return True
        return False

    def update_section(self, section: Section) -> bool:
        for row, current in enumerate(self._sections):
            if current.index == section.index:
                self._sections[row] = section
                self._recompute_warnings()
                self.dataChanged.emit(self.index(0, 0), self.index(len(self._sections) - 1, 0), list(self._roles))
                return True
        return False

    @Slot(int, result=int)
    def rowForSection(self, section_index: int) -> int:
        for row, section in enumerate(self._sections):
            if section.index == section_index:
                return row
        return -1

    @Slot(int, result=str)
    def timeLabelForRow(self, row: int) -> str:
        if not 0 <= row < len(self._sections):
            return ""
        section = self._sections[row]
        return f"{section.start_time}–{section.end_time}"

    def section_at(self, section_index: int) -> Section | None:
        return next((section for section in self._sections if section.index == section_index), None)

    def all_sections(self) -> list[Section]:
        return list(self._sections)


class RecognitionCandidateModel(QAbstractListModel):
    """Small confirmation-list model; it is not a second course editor."""

    NameRole = Qt.UserRole + 1
    WeekdayLabelRole = Qt.UserRole + 2
    ScheduleLabelRole = Qt.UserRole + 3
    WeekLabelRole = Qt.UserRole + 4
    LocationTextRole = Qt.UserRole + 5
    TeacherRole = Qt.UserRole + 6
    NeedsReviewRole = Qt.UserRole + 7
    ReviewFieldsRole = Qt.UserRole + 8
    NotesRole = Qt.UserRole + 9

    _roles = {
        NameRole: b"name",
        WeekdayLabelRole: b"weekdayLabel",
        ScheduleLabelRole: b"scheduleLabel",
        WeekLabelRole: b"weekLabel",
        LocationTextRole: b"locationText",
        TeacherRole: b"teacher",
        NeedsReviewRole: b"needsReview",
        ReviewFieldsRole: b"reviewFields",
        NotesRole: b"notes",
    }
    countChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._courses: list[CandidateCourse] = []

    def roleNames(self) -> dict[int, bytes]:
        return self._roles

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._courses)

    @Property(int, constant=False)
    def count(self) -> int:
        return len(self._courses)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._courses):
            return None
        course = self._courses[index.row()]
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday_label = weekday_names[course.weekday - 1] if course.weekday and 1 <= course.weekday <= 7 else "待确认星期"
        section_label = (
            f"第{course.start_section}–{course.end_section}节"
            if course.start_section is not None and course.end_section is not None
            else "节次待确认"
        )
        if course.week_pattern == "custom":
            week_label = "、".join(str(week) for week in course.custom_weeks) + "周"
        elif course.start_week is not None and course.end_week is not None:
            pattern = {"all": "每周", "odd": "单周", "even": "双周"}.get(course.week_pattern, "待确认")
            week_label = f"{course.start_week}–{course.end_week}周（{pattern}）"
        else:
            week_label = "周次待确认"
        values = {
            self.NameRole: course.name,
            self.WeekdayLabelRole: weekday_label,
            self.ScheduleLabelRole: section_label,
            self.WeekLabelRole: week_label,
            self.LocationTextRole: course.location_text or "未填写地点",
            self.TeacherRole: course.teacher or "未填写教师",
            self.NeedsReviewRole: course.needs_review,
            self.ReviewFieldsRole: list(course.needs_review_fields),
            self.NotesRole: course.notes,
        }
        return values.get(role)

    def refresh(self, courses: list[CandidateCourse]) -> None:
        self.beginResetModel()
        self._courses = list(courses)
        self.endResetModel()
        self.countChanged.emit()

    def clear(self) -> None:
        self.refresh([])

    def candidate_at(self, row: int) -> CandidateCourse | None:
        return self._courses[row] if 0 <= row < len(self._courses) else None

    def all_candidates(self) -> list[CandidateCourse]:
        return list(self._courses)
