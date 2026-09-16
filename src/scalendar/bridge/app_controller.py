"""The application lifecycle and the typed Python-to-QML bridge."""

from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import re

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot, QUrl

from scalendar.bridge.course_editor import CourseEditorState
from scalendar.bridge.qt_models import CourseListModel, SectionListModel, TimetableLayoutModel
from scalendar.core.models import Course, ProjectDocument, Section
from scalendar.core.validation import TIME_RE, validate_project
from scalendar.storage.project_store import ProjectStore


def _local_path(value: str) -> Path:
    if value.startswith("file:"):
        return Path(QUrl(value).toLocalFile())
    return Path(value)


def _slug(value: str) -> str:
    compact = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", value.strip(), flags=re.UNICODE).strip("-")
    return compact or "untitled"


class AppController(QObject):
    """Own the active project and expose only typed models/state to QML."""

    pageRequested = Signal(str)
    toastRequested = Signal(str)
    errorRequested = Signal(str)
    savePathRequested = Signal()
    projectChanged = Signal()
    dirtyChanged = Signal()
    projectPathChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._project: ProjectDocument | None = None
        self._project_path = ""
        self._dirty = False
        self._store = ProjectStore()
        self._course_model = CourseListModel(self)
        self._section_model = SectionListModel(self)
        self._timetable_layout = TimetableLayoutModel(self)
        self._course_editor = CourseEditorState(self)
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(850)
        self._autosave_timer.timeout.connect(self._autosave)

    @Property(str, notify=projectChanged)
    def projectName(self) -> str:
        return self._project.project_name if self._project else "未命名项目"

    @Property(str, notify=projectChanged)
    def semesterName(self) -> str:
        return self._project.semester.name if self._project else "未命名学期"

    @Property(str, notify=projectChanged)
    def firstWeekMonday(self) -> str:
        return self._project.semester.first_week_monday if self._project else ""

    @Property(int, notify=projectChanged)
    def totalWeeks(self) -> int:
        return self._project.semester.total_weeks if self._project else 0

    @Property(str, notify=projectPathChanged)
    def projectPath(self) -> str:
        return self._project_path

    @Property(bool, notify=dirtyChanged)
    def dirty(self) -> bool:
        return self._dirty

    @Property(QObject, constant=True)
    def courseModel(self) -> CourseListModel:
        return self._course_model

    @Property(QObject, constant=True)
    def sectionModel(self) -> SectionListModel:
        return self._section_model

    @Property(QObject, constant=True)
    def timetableLayout(self) -> TimetableLayoutModel:
        return self._timetable_layout

    @Property(QObject, constant=True)
    def courseEditor(self) -> CourseEditorState:
        return self._course_editor

    @Slot(str, str, str, int, result=bool)
    def createProject(self, project_name: str, semester_name: str, first_week_monday: str, total_weeks: int) -> bool:
        project_name = project_name.strip()
        semester_name = semester_name.strip()
        try:
            monday = date.fromisoformat(first_week_monday.strip())
        except ValueError:
            self.errorRequested.emit("第一教学周周一必须是 YYYY-MM-DD 日期。")
            return False
        if monday.weekday() != 0:
            self.errorRequested.emit("第一教学周周一必须是周一。")
            return False
        if not project_name or not semester_name:
            self.errorRequested.emit("请填写项目名称和学期名称。")
            return False
        if not 1 <= int(total_weeks) <= 60:
            self.errorRequested.emit("教学周数应在 1 到 60 周之间。")
            return False
        project = ProjectDocument.blank(project_name)
        project.semester.name = semester_name
        project.semester.first_week_monday = monday.isoformat()
        project.semester.total_weeks = int(total_weeks)
        self._set_project(project, "")
        self._set_dirty(True)
        self.pageRequested.emit("timetable")
        self.toastRequested.emit("已创建空白课表，请添加第一门课程。")
        return True

    @Slot(str, result=bool)
    def openProject(self, path: str) -> bool:
        try:
            source = _local_path(path)
            project = self._store.load(source)
        except (OSError, ValueError, TypeError) as exc:
            self.errorRequested.emit(f"无法打开项目：{exc}")
            return False
        self._set_project(project, str(source))
        self._set_dirty(False)
        self.pageRequested.emit("timetable")
        self.toastRequested.emit("项目已打开。")
        return True

    @Slot(result=bool)
    def save(self) -> bool:
        if not self._project:
            self.errorRequested.emit("还没有可保存的项目。")
            return False
        if not self._project_path:
            self.savePathRequested.emit()
            return False
        return self._save_to_path(Path(self._project_path))

    @Slot(str, result=bool)
    def saveAs(self, path: str) -> bool:
        if not self._project:
            self.errorRequested.emit("还没有可保存的项目。")
            return False
        target = _local_path(path)
        if target.suffix.lower() != ".scalendar":
            target = target.with_suffix(".scalendar")
        if self._save_to_path(target):
            self._project_path = str(target)
            self.projectPathChanged.emit()
            return True
        return False

    @Slot()
    def flushAutosave(self) -> None:
        self._autosave()

    @Slot(str)
    def beginEditCourse(self, course_id: str) -> None:
        if not self._project:
            self.errorRequested.emit("请先创建或打开一个项目。")
            return
        course = self._course_model.course_at(course_id)
        if course is None:
            self.errorRequested.emit("找不到要编辑的课程。")
            return
        self._course_editor.load(course, self._project.semester.total_weeks)

    @Slot()
    def beginNewCourse(self) -> None:
        if not self._project:
            self.errorRequested.emit("请先创建或打开一个项目。")
            return
        self._course_editor.load(None, self._project.semester.total_weeks)

    @Slot(result=bool)
    def saveEditor(self) -> bool:
        if not self._project:
            self.errorRequested.emit("请先创建或打开一个项目。")
            return False
        course = self._course_editor.to_course(self._project.semester.total_weeks)
        issues = validate_project(
            ProjectDocument(
                schema_version=self._project.schema_version,
                project_name=self._project.project_name,
                semester=self._project.semester,
                sections=self._project.sections,
                courses=[item for item in self._project.courses if item.id != course.id] + [course],
                created_at=self._project.created_at,
                updated_at=self._project.updated_at,
            )
        )
        if issues:
            self.errorRequested.emit("课程无法保存：" + "；".join(str(issue) for issue in issues))
            return False
        existing = self._course_model.course_at(course.id)
        if existing is None:
            self._project.courses.append(course)
            self._course_model.append_course(course)
            message = "课程已添加。"
        else:
            for index, item in enumerate(self._project.courses):
                if item.id == course.id:
                    self._project.courses[index] = course
                    break
            self._course_model.update_course(course)
            message = "课程已更新。"
        self._set_dirty(True)
        self.toastRequested.emit(message)
        return True

    @Slot(str, result=bool)
    def deleteCourse(self, course_id: str) -> bool:
        if not self._project:
            return False
        before = len(self._project.courses)
        self._project.courses = [course for course in self._project.courses if course.id != course_id]
        if len(self._project.courses) == before:
            return False
        self._course_model.remove_course(course_id)
        self._set_dirty(True)
        self.toastRequested.emit("课程已删除。")
        return True

    @Slot(int, str, str, result=bool)
    def updateSection(self, section_index: int, start_time: str, end_time: str) -> bool:
        if not self._project:
            return False
        if not TIME_RE.fullmatch(start_time) or not TIME_RE.fullmatch(end_time) or start_time >= end_time:
            self.errorRequested.emit("节次时间必须使用 HH:MM，且结束时间晚于开始时间。")
            return False
        for row, current in enumerate(self._project.sections):
            if current.index == section_index:
                updated = Section(current.index, start_time, end_time, current.label)
                self._project.sections[row] = updated
                self._section_model.update_section(updated)
                self._set_dirty(True)
                return True
        self.errorRequested.emit("找不到要修改的节次。")
        return False

    @Slot(str)
    def notify(self, message: str) -> None:
        self.toastRequested.emit(message)

    def _set_project(self, project: ProjectDocument, path: str) -> None:
        self._project = project
        self._project_path = path
        self._course_model.refresh(project.courses)
        self._section_model.refresh(project.sections)
        self._course_editor.reset()
        self.projectChanged.emit()
        self.projectPathChanged.emit()

    def _set_dirty(self, value: bool) -> None:
        if self._dirty != value:
            self._dirty = value
            self.dirtyChanged.emit()
        if value:
            self._autosave_timer.start()

    def _autosave(self) -> None:
        if self._dirty and self._project and self._project_path:
            self._save_to_path(Path(self._project_path), quiet=True)

    def _save_to_path(self, path: Path, quiet: bool = False) -> bool:
        try:
            self._store.save(self._project, path)
        except (OSError, ValueError, TypeError) as exc:
            self.errorRequested.emit(f"保存失败：{exc}")
            return False
        self._project_path = str(path)
        self._set_dirty(False)
        self.projectPathChanged.emit()
        if not quiet:
            self.toastRequested.emit("项目已保存。")
        return True

    @staticmethod
    def default_project_directory() -> Path:
        base = os.environ.get("LOCALAPPDATA") or str(Path.home())
        return Path(base) / "Scalendar" / "projects"

    def default_project_path(self) -> Path:
        return self.default_project_directory() / f"{_slug(self.projectName)}.scalendar"
