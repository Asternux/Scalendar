"""Qt list models used by the QML editor.

The QML layer receives role-based values from these models rather than a
collection of Python dictionaries. The core dataclasses remain independent of
Qt and are still the source of truth.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Slot, QObject, Property

from scalendar.core.models import Course, ProjectDocument, Section
from scalendar.core.timetable_layout import DEFAULT_TIMETABLE_LAYOUT


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
    }

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._courses: list[Course] = []

    def roleNames(self) -> dict[int, bytes]:
        return self._roles

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._courses)

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
        }
        return values.get(role)

    def refresh(self, courses: list[Course]) -> None:
        self.beginResetModel()
        self._courses = list(courses)
        self.endResetModel()

    def append_course(self, course: Course) -> None:
        row = len(self._courses)
        self.beginInsertRows(QModelIndex(), row, row)
        self._courses.append(course)
        self.endInsertRows()

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
                return True
        return False

    def course_at(self, course_id: str) -> Course | None:
        return next((course for course in self._courses if course.id == course_id), None)

    def all_courses(self) -> list[Course]:
        return list(self._courses)


class SectionListModel(QAbstractListModel):
    IndexRole = Qt.UserRole + 1
    StartTimeRole = Qt.UserRole + 2
    EndTimeRole = Qt.UserRole + 3
    LabelRole = Qt.UserRole + 4

    _roles = {
        IndexRole: b"sectionIndex",
        StartTimeRole: b"startTime",
        EndTimeRole: b"endTime",
        LabelRole: b"label",
    }

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._sections: list[Section] = []

    def roleNames(self) -> dict[int, bytes]:
        return self._roles

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._sections)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._sections):
            return None
        section = self._sections[index.row()]
        return {
            self.IndexRole: section.index,
            self.StartTimeRole: section.start_time,
            self.EndTimeRole: section.end_time,
            self.LabelRole: section.label,
        }.get(role)

    def refresh(self, sections: list[Section]) -> None:
        self.beginResetModel()
        self._sections = list(sections)
        self.endResetModel()

    def update_section(self, section: Section) -> bool:
        for row, current in enumerate(self._sections):
            if current.index == section.index:
                self._sections[row] = section
                index = self.index(row, 0)
                self.dataChanged.emit(index, index, list(self._roles))
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
