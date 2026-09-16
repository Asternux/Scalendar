"""Typed, unsaved editor state for the course drawer."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot

from scalendar.core.models import Course, new_id


class CourseEditorState(QObject):
    courseIdChanged = Signal()
    nameChanged = Signal()
    weekdayChanged = Signal()
    startSectionChanged = Signal()
    endSectionChanged = Signal()
    startWeekChanged = Signal()
    endWeekChanged = Signal()
    weekPatternChanged = Signal()
    customWeeksTextChanged = Signal()
    teacherChanged = Signal()
    buildingChanged = Signal()
    roomChanged = Signal()
    locationTextChanged = Signal()
    colorChanged = Signal()
    notesChanged = Signal()
    recognitionStatusChanged = Signal()
    hasCourseChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._course_id = ""
        self._has_course = False
        self._name = ""
        self._weekday = 1
        self._start_section = 1
        self._end_section = 1
        self._start_week = 1
        self._end_week = 20
        self._week_pattern = "all"
        self._custom_weeks_text = ""
        self._teacher = ""
        self._building = ""
        self._room = ""
        self._location_text = ""
        self._color = "#6C8EF5"
        self._notes = ""
        self._recognition_status = "manual"

    def _set(self, attr: str, value: object, signal: Signal) -> None:
        if getattr(self, attr) != value:
            setattr(self, attr, value)
            signal.emit()

    @Property(str, notify=courseIdChanged)
    def courseId(self) -> str:
        return self._course_id

    @Property(bool, notify=hasCourseChanged)
    def hasCourse(self) -> bool:
        return self._has_course

    @Property(str, notify=nameChanged)
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._set("_name", str(value), self.nameChanged)

    @Property(int, notify=weekdayChanged)
    def weekday(self) -> int:
        return self._weekday

    @weekday.setter
    def weekday(self, value: int) -> None:
        self._set("_weekday", int(value), self.weekdayChanged)

    @Property(int, notify=startSectionChanged)
    def startSection(self) -> int:
        return self._start_section

    @startSection.setter
    def startSection(self, value: int) -> None:
        self._set("_start_section", int(value), self.startSectionChanged)

    @Property(int, notify=endSectionChanged)
    def endSection(self) -> int:
        return self._end_section

    @endSection.setter
    def endSection(self, value: int) -> None:
        self._set("_end_section", int(value), self.endSectionChanged)

    @Property(int, notify=startWeekChanged)
    def startWeek(self) -> int:
        return self._start_week

    @startWeek.setter
    def startWeek(self, value: int) -> None:
        self._set("_start_week", int(value), self.startWeekChanged)

    @Property(int, notify=endWeekChanged)
    def endWeek(self) -> int:
        return self._end_week

    @endWeek.setter
    def endWeek(self, value: int) -> None:
        self._set("_end_week", int(value), self.endWeekChanged)

    @Property(str, notify=weekPatternChanged)
    def weekPattern(self) -> str:
        return self._week_pattern

    @weekPattern.setter
    def weekPattern(self, value: str) -> None:
        self._set("_week_pattern", str(value), self.weekPatternChanged)

    @Property(str, notify=customWeeksTextChanged)
    def customWeeksText(self) -> str:
        return self._custom_weeks_text

    @customWeeksText.setter
    def customWeeksText(self, value: str) -> None:
        self._set("_custom_weeks_text", str(value), self.customWeeksTextChanged)

    @Property(str, notify=teacherChanged)
    def teacher(self) -> str:
        return self._teacher

    @teacher.setter
    def teacher(self, value: str) -> None:
        self._set("_teacher", str(value), self.teacherChanged)

    @Property(str, notify=buildingChanged)
    def building(self) -> str:
        return self._building

    @building.setter
    def building(self, value: str) -> None:
        self._set("_building", str(value), self.buildingChanged)

    @Property(str, notify=roomChanged)
    def room(self) -> str:
        return self._room

    @room.setter
    def room(self, value: str) -> None:
        self._set("_room", str(value), self.roomChanged)

    @Property(str, notify=locationTextChanged)
    def locationText(self) -> str:
        return self._location_text

    @locationText.setter
    def locationText(self, value: str) -> None:
        self._set("_location_text", str(value), self.locationTextChanged)

    @Property(str, notify=colorChanged)
    def color(self) -> str:
        return self._color

    @color.setter
    def color(self, value: str) -> None:
        self._set("_color", str(value), self.colorChanged)

    @Property(str, notify=notesChanged)
    def notes(self) -> str:
        return self._notes

    @notes.setter
    def notes(self, value: str) -> None:
        self._set("_notes", str(value), self.notesChanged)

    @Property(str, notify=recognitionStatusChanged)
    def recognitionStatus(self) -> str:
        return self._recognition_status

    @recognitionStatus.setter
    def recognitionStatus(self, value: str) -> None:
        self._set("_recognition_status", str(value), self.recognitionStatusChanged)

    @Slot(int)
    def setWeekPatternIndex(self, index: int) -> None:
        self.weekPattern = ["all", "odd", "even", "custom"][max(0, min(3, index))]

    @Slot()
    def reset(self) -> None:
        self.load(None, 20)

    def load(self, course: Course | None, total_weeks: int) -> None:
        if course is None:
            values = Course(id="", name="", end_week=total_weeks)
            course_id = ""
            has_course = False
        else:
            values = course
            course_id = course.id
            has_course = True
        self._course_id = course_id
        self.courseIdChanged.emit()
        self._has_course = has_course
        self.hasCourseChanged.emit()
        self.name = values.name
        self.weekday = values.weekday
        self.startSection = values.start_section
        self.endSection = values.end_section
        self.startWeek = values.start_week
        self.endWeek = values.end_week
        self.weekPattern = values.week_pattern
        self.customWeeksText = ", ".join(str(week) for week in values.custom_weeks)
        self.teacher = values.teacher
        self.building = values.building
        self.room = values.room
        self.locationText = values.location_text
        self.color = values.color
        self.notes = values.notes
        self.recognitionStatus = values.recognition_status

    def to_course(self, total_weeks: int) -> Course:
        custom_weeks = []
        for item in self._custom_weeks_text.replace("，", ",").split(","):
            item = item.strip()
            if item:
                try:
                    custom_weeks.append(int(item))
                except ValueError:
                    continue
        return Course(
            id=self._course_id or new_id(),
            name=self._name.strip(),
            weekday=self._weekday,
            start_section=self._start_section,
            end_section=self._end_section,
            start_week=self._start_week,
            end_week=self._end_week or total_weeks,
            week_pattern=self._week_pattern,
            custom_weeks=custom_weeks,
            teacher=self._teacher.strip(),
            building=self._building.strip(),
            room=self._room.strip(),
            location_text=self._location_text.strip(),
            color=self._color.strip() or "#6C8EF5",
            notes=self._notes.strip(),
            recognition_status=self._recognition_status or "manual",
        )
