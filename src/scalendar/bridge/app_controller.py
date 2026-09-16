"""The application lifecycle and the typed Python-to-QML bridge."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta
import os
from pathlib import Path
import re

from PySide6.QtCore import QObject, Property, QRunnable, QThreadPool, QTimer, Signal, Slot, QUrl
from PySide6.QtGui import QImageReader

from scalendar.bridge.course_editor import CourseEditorState
from scalendar.bridge.qt_models import CourseListModel, CourseSortProxyModel, RecognitionCandidateModel, SectionListModel, TimetableLayoutModel
from scalendar.core.models import Course, ProjectDocument, Section
from scalendar.core.validation import PATTERNS, TIME_RE, parse_custom_weeks, validate_project
from scalendar.exporters.xlsx import ExcelExportError, export_project_to_xlsx
from scalendar.importers.xlsx import ExcelImportError, ExcelImportResult, import_xlsx
from scalendar.recognition.base import RecognitionContext, RecognitionError, RecognitionProvider
from scalendar.recognition.models import RecognitionResult
from scalendar.recognition.normalizer import candidate_to_course
from scalendar.recognition.openai_vision import OpenAIVisionProvider, SUPPORTED_IMAGE_TYPES
from scalendar.storage.project_store import ProjectStore


def _local_path(value: str) -> Path:
    if value.startswith("file:"):
        return Path(QUrl(value).toLocalFile())
    return Path(value)


def _slug(value: str) -> str:
    compact = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", value.strip(), flags=re.UNICODE).strip("-")
    return compact or "untitled"


class _RecognitionWorkerSignals(QObject):
    finished = Signal(object)
    failed = Signal(object)


class _RecognitionWorker(QRunnable):
    def __init__(self, provider: RecognitionProvider, image: Path, context: RecognitionContext) -> None:
        super().__init__()
        self.provider = provider
        self.image = image
        self.context = context
        self.signals = _RecognitionWorkerSignals()

    def run(self) -> None:
        try:
            self.signals.finished.emit(self.provider.recognize(self.image, self.context))
        except RecognitionError as exc:
            self.signals.failed.emit(exc)
        except Exception:
            self.signals.failed.emit(RecognitionError("api_error", "识别服务暂时不可用。"))


class AppController(QObject):
    """Own the active project and expose only typed models/state to QML."""

    pageRequested = Signal(str)
    toastRequested = Signal(str)
    errorRequested = Signal(str)
    savePathRequested = Signal()
    projectChanged = Signal()
    dirtyChanged = Signal()
    projectPathChanged = Signal()
    imageChanged = Signal()
    recognitionChanged = Signal()
    apiKeyChanged = Signal()
    excelChanged = Signal()

    def __init__(self, recognition_provider: RecognitionProvider | None = None) -> None:
        super().__init__()
        self._project: ProjectDocument | None = None
        self._project_path = ""
        self._dirty = False
        self._store = ProjectStore()
        self._course_model = CourseListModel(self)
        self._course_sort_model = CourseSortProxyModel(self)
        self._course_sort_model.setSourceModel(self._course_model)
        self._recognition_candidate_model = RecognitionCandidateModel(self)
        self._excel_candidate_model = RecognitionCandidateModel(self)
        self._section_model = SectionListModel(self)
        self._timetable_layout = TimetableLayoutModel(self)
        self._course_editor = CourseEditorState(self)
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(850)
        self._autosave_timer.timeout.connect(self._autosave)
        self._recognition_provider = recognition_provider or OpenAIVisionProvider()
        self._recognition_pool = QThreadPool.globalInstance()
        self._recognition_worker: _RecognitionWorker | None = None
        self._image_path = Path()
        self._image_name = ""
        self._image_preview_url = ""
        self._image_width = 0
        self._image_height = 0
        self._recognition_state = "idle"
        self._recognition_phase = ""
        self._recognition_error_text = ""
        self._pending_recognition: RecognitionResult | None = None
        self._excel_file_path = Path()
        self._excel_file_name = ""
        self._excel_sheet_count = 0
        self._excel_format_text = ""
        self._excel_state = "idle"
        self._excel_error_text = ""
        self._pending_excel: ExcelImportResult | None = None
        self._session_api_key = ""
        self._session_model = os.environ.get("OPENAI_MODEL", "gpt-5.5")

    @Property(str, notify=projectChanged)
    def projectName(self) -> str:
        return self._project.project_name if self._project else "未命名项目"

    @Property(bool, notify=projectChanged)
    def hasProject(self) -> bool:
        return self._project is not None

    @Property(str, notify=projectChanged)
    def school(self) -> str:
        return self._project.school if self._project else ""

    @Property(str, notify=projectChanged)
    def campus(self) -> str:
        return self._project.campus if self._project else ""

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
    def courseSortModel(self) -> CourseSortProxyModel:
        return self._course_sort_model

    @Property(QObject, constant=True)
    def sectionModel(self) -> SectionListModel:
        return self._section_model

    @Property(QObject, constant=True)
    def timetableLayout(self) -> TimetableLayoutModel:
        return self._timetable_layout

    @Property(QObject, constant=True)
    def courseEditor(self) -> CourseEditorState:
        return self._course_editor

    @Property(QObject, constant=True)
    def recognitionCandidateModel(self) -> RecognitionCandidateModel:
        return self._recognition_candidate_model

    @Property(str, notify=imageChanged)
    def imageName(self) -> str:
        return self._image_name

    @Property(str, notify=imageChanged)
    def imagePreviewUrl(self) -> str:
        return self._image_preview_url

    @Property(int, notify=imageChanged)
    def imageWidth(self) -> int:
        return self._image_width

    @Property(int, notify=imageChanged)
    def imageHeight(self) -> int:
        return self._image_height

    @Property(bool, notify=imageChanged)
    def hasImage(self) -> bool:
        return bool(self._image_path)

    @Property(str, notify=recognitionChanged)
    def recognitionState(self) -> str:
        return self._recognition_state

    @Property(str, notify=recognitionChanged)
    def recognitionPhase(self) -> str:
        return self._recognition_phase

    @Property(str, notify=recognitionChanged)
    def recognitionErrorText(self) -> str:
        return self._recognition_error_text

    @Property(int, notify=recognitionChanged)
    def recognitionCourseCount(self) -> int:
        return len(self._pending_recognition.courses) if self._pending_recognition else 0

    @Property(int, notify=recognitionChanged)
    def recognitionReviewCount(self) -> int:
        return self._pending_recognition.review_count if self._pending_recognition else 0

    @Property(QObject, constant=True)
    def excelCandidateModel(self) -> RecognitionCandidateModel:
        return self._excel_candidate_model

    @Property(str, notify=excelChanged)
    def excelFileName(self) -> str:
        return self._excel_file_name

    @Property(int, notify=excelChanged)
    def excelSheetCount(self) -> int:
        return self._excel_sheet_count

    @Property(str, notify=excelChanged)
    def excelFormatText(self) -> str:
        return self._excel_format_text

    @Property(str, notify=excelChanged)
    def excelState(self) -> str:
        return self._excel_state

    @Property(str, notify=excelChanged)
    def excelErrorText(self) -> str:
        return self._excel_error_text

    @Property(int, notify=excelChanged)
    def excelCourseCount(self) -> int:
        return len(self._pending_excel.candidates) if self._pending_excel else 0

    @Property(int, notify=excelChanged)
    def excelReviewCount(self) -> int:
        return sum(1 for candidate in self._pending_excel.candidates if candidate.needs_review) if self._pending_excel else 0

    @Property(bool, notify=apiKeyChanged)
    def hasApiKey(self) -> bool:
        return bool(self._session_api_key or os.environ.get("OPENAI_API_KEY", "").strip())

    @Property(str, notify=apiKeyChanged)
    def apiKeyStatus(self) -> str:
        return "已设置（仅本次运行）" if self.hasApiKey else "未设置"

    @Property(str, notify=apiKeyChanged)
    def openaiModel(self) -> str:
        return self._session_model

    @Slot(str)
    def navigate(self, page: str) -> None:
        self.pageRequested.emit(page)

    @Slot(int)
    def setCourseSort(self, mode: int) -> None:
        self._course_sort_model.setSortMode(mode)

    @Slot(str, result=bool)
    def setApiKey(self, value: str) -> bool:
        self._session_api_key = str(value or "").strip()
        if hasattr(self._recognition_provider, "api_key"):
            self._recognition_provider.api_key = self._session_api_key or None
        self.apiKeyChanged.emit()
        self.toastRequested.emit("API Key 仅保存在本次运行内存中。")
        return True

    @Slot(str, result=bool)
    def setOpenAIModel(self, value: str) -> bool:
        model = str(value or "").strip()
        if not model:
            self.errorRequested.emit("模型名称不能为空。")
            return False
        self._session_model = model
        if hasattr(self._recognition_provider, "model"):
            self._recognition_provider.model = model
        self.apiKeyChanged.emit()
        return True

    @Slot(str, result=bool)
    def updateProjectContext(self, school: str, campus: str) -> bool:
        if not self._project:
            self.errorRequested.emit("请先创建或打开一个项目。")
            return False
        self._project.school = str(school or "").strip()
        self._project.campus = str(campus or "").strip()
        self.projectChanged.emit()
        self._set_dirty(True)
        self.toastRequested.emit("学校与校区信息已更新。")
        return True

    @Slot(str, result=bool)
    def selectImage(self, path: str) -> bool:
        source = _local_path(str(path))
        if source.suffix.lower() not in SUPPORTED_IMAGE_TYPES:
            self._set_image_error("图片格式无法读取，请选择 PNG、JPG、JPEG 或 WEBP。")
            return False
        if not source.is_file():
            self._set_image_error("找不到所选图片。")
            return False
        reader = QImageReader(str(source))
        size = reader.size()
        if not reader.canRead() or size.width() <= 0 or size.height() <= 0:
            self._set_image_error("图片格式无法读取或图片已损坏。")
            return False
        self._image_path = source
        self._image_name = source.name
        self._image_preview_url = QUrl.fromLocalFile(str(source)).toString()
        self._image_width = size.width()
        self._image_height = size.height()
        self._pending_recognition = None
        self._recognition_candidate_model.clear()
        self._recognition_state = "ready"
        self._recognition_phase = "已选择图片"
        self._recognition_error_text = ""
        self.imageChanged.emit()
        self.recognitionChanged.emit()
        return True

    @Slot()
    def clearImage(self) -> None:
        self._image_path = Path()
        self._image_name = ""
        self._image_preview_url = ""
        self._image_width = 0
        self._image_height = 0
        self._pending_recognition = None
        self._recognition_candidate_model.clear()
        self._recognition_state = "idle"
        self._recognition_phase = ""
        self._recognition_error_text = ""
        self.imageChanged.emit()
        self.recognitionChanged.emit()

    @Slot(result=bool)
    def startRecognition(self) -> bool:
        if not self._project:
            self._set_recognition_error("project_required", "请先创建或打开一个项目。")
            return False
        if not self._image_path:
            self._set_recognition_error("invalid_image", "请先选择一张课表图片。")
            return False
        if self._recognition_state == "recognizing":
            return False
        provider = self._recognition_provider
        api_key = self._session_api_key or os.environ.get("OPENAI_API_KEY", "").strip()
        if provider.requires_api_key and not api_key:
            self._set_recognition_error("missing_api_key", "未设置 API Key。请先在设置中填写 OpenAI API Key。")
            return False
        if hasattr(provider, "api_key"):
            provider.api_key = api_key or None
        if hasattr(provider, "model"):
            provider.model = self._session_model
        context = RecognitionContext(
            school=self.school,
            campus=self.campus,
            total_weeks=self.totalWeeks,
            section_indices=tuple(section.index for section in self._project.sections),
        )
        self._pending_recognition = None
        self._recognition_candidate_model.clear()
        self._recognition_state = "recognizing"
        self._recognition_phase = "正在读取课表结构……"
        self._recognition_error_text = ""
        self.recognitionChanged.emit()
        worker = _RecognitionWorker(provider, self._image_path, context)
        worker.signals.finished.connect(self._on_recognition_finished)
        worker.signals.failed.connect(self._on_recognition_failed)
        self._recognition_worker = worker
        self._recognition_pool.start(worker)
        return True

    @Slot()
    def cancelRecognition(self) -> None:
        self._pending_recognition = None
        self._recognition_candidate_model.clear()
        self._recognition_state = "ready" if self._image_path else "idle"
        self._recognition_phase = "已选择图片" if self._image_path else ""
        self._recognition_error_text = ""
        self.recognitionChanged.emit()

    @Slot(result=bool)
    def applyRecognitionResult(self) -> bool:
        if not self._project or not self._pending_recognition:
            self.errorRequested.emit("没有可导入的识别结果。")
            return False
        section_indices = tuple(section.index for section in self._project.sections)
        new_courses = [
            candidate_to_course(candidate, self._project.semester.total_weeks, section_indices)
            for candidate in self._pending_recognition.courses
        ]
        candidate_project = deepcopy(self._project)
        candidate_project.courses.extend(new_courses)
        issues = validate_project(candidate_project)
        if issues:
            self.errorRequested.emit("识别结果无法导入：" + "；".join(str(issue) for issue in issues))
            return False
        self._project.courses.extend(new_courses)
        for course in new_courses:
            self._course_model.append_course(course)
        count = len(new_courses)
        self._pending_recognition = None
        self._recognition_candidate_model.clear()
        self._recognition_state = "ready" if self._image_path else "idle"
        self._recognition_phase = "识别结果已导入"
        self._recognition_error_text = ""
        self._set_dirty(True)
        self.recognitionChanged.emit()
        self.pageRequested.emit("timetable")
        self.toastRequested.emit(f"已向当前课表新增 {count} 门课程。")
        return True

    @Slot(str, result=bool)
    def selectExcel(self, path: str) -> bool:
        source = _local_path(str(path))
        if source.suffix.lower() != ".xlsx":
            self._set_excel_error("not_xlsx", "请选择 XLSX 文件。")
            return False
        try:
            result = import_xlsx(source)
        except ExcelImportError as exc:
            self._set_excel_error(exc.code, exc.message)
            return False
        self.clearImage()
        self._excel_file_path = source
        self._excel_file_name = source.name
        self._excel_sheet_count = len(result.sheet_names)
        self._excel_format_text = result.format_text
        self._excel_state = "ready_to_import"
        self._excel_error_text = ""
        self._pending_excel = result
        self._excel_candidate_model.refresh(result.candidates)
        self.excelChanged.emit()
        return True

    @Slot()
    def clearExcel(self) -> None:
        self._excel_file_path = Path()
        self._excel_file_name = ""
        self._excel_sheet_count = 0
        self._excel_format_text = ""
        self._excel_state = "idle"
        self._excel_error_text = ""
        self._pending_excel = None
        self._excel_candidate_model.clear()
        self.excelChanged.emit()

    @Slot(result=bool)
    def applyExcelImport(self) -> bool:
        if not self._project or not self._pending_excel:
            self.errorRequested.emit("没有可导入的 Excel 结果。")
            return False
        result = self._pending_excel
        blank_project = not self._project.courses
        candidate_project = deepcopy(self._project)
        if blank_project and result.workbook_kind == "standard":
            candidate_project.project_name = result.project_name
            candidate_project.semester.name = result.semester_name
            candidate_project.semester.first_week_monday = result.first_week_monday
            candidate_project.semester.total_weeks = result.total_weeks
            candidate_project.school = result.school
            candidate_project.campus = result.campus
            if result.sections:
                candidate_project.sections = list(result.sections)
        section_indices = tuple(section.index for section in candidate_project.sections)
        new_courses = [
            candidate_to_course(candidate, candidate_project.semester.total_weeks, section_indices)
            for candidate in result.candidates
        ]
        candidate_project.courses.extend(new_courses)
        issues = validate_project(candidate_project)
        if issues:
            self.errorRequested.emit("Excel 结果无法导入：" + "；".join(str(issue) for issue in issues))
            return False
        self._project.semester = candidate_project.semester
        self._project.project_name = candidate_project.project_name
        self._project.school = candidate_project.school
        self._project.campus = candidate_project.campus
        self._project.sections = candidate_project.sections
        self._project.courses.extend(new_courses)
        self._section_model.refresh(self._project.sections)
        for course in new_courses:
            self._course_model.append_course(course)
        count = len(new_courses)
        self.clearExcel()
        self._set_dirty(True)
        self.projectChanged.emit()
        self.pageRequested.emit("timetable")
        self.toastRequested.emit(f"已从 Excel 新增 {count} 门课程。")
        return True

    @Slot(str, result=bool)
    def exportExcel(self, path: str) -> bool:
        if not self._project:
            self.errorRequested.emit("还没有可导出的项目。")
            return False
        target = _local_path(path)
        if target.suffix.lower() != ".xlsx":
            target = target.with_suffix(".xlsx")
        try:
            export_project_to_xlsx(self._project, target)
        except ExcelExportError as exc:
            self.errorRequested.emit(exc.message)
            return False
        self.toastRequested.emit(f"Excel 已导出：{target.name}")
        return True

    def _set_excel_error(self, code: str, message: str) -> None:
        messages = {
            "file_not_found": "找不到 Excel 文件。",
            "file_corrupt": "Excel 文件损坏或不是有效的 XLSX 文件。",
            "not_xlsx": "请选择 XLSX 文件。",
            "missing_courses": "缺少必要 Sheet：Courses。",
            "missing_settings": "缺少必要 Sheet：Settings。",
            "missing_columns": "Courses Sheet 缺少必要列。",
            "invalid_cell": "Excel 中存在格式错误的单元格。",
            "out_of_range": "Excel 中存在超出项目范围的课程数据。",
            "unrecognized_structure": "无法可靠识别该 Excel 的课表结构。",
            "no_courses": "Excel 中没有可导入的课程。",
            "invalid_settings": "Excel 的学期设置无效。",
        }
        self._excel_state = "error"
        self._excel_error_text = messages.get(code, message)
        self._pending_excel = None
        self._excel_candidate_model.clear()
        self.excelChanged.emit()
        self.errorRequested.emit(self._excel_error_text)

    def _set_image_error(self, message: str) -> None:
        self._recognition_state = "error"
        self._recognition_error_text = message
        self._recognition_phase = ""
        self.errorRequested.emit(message)
        self.imageChanged.emit()
        self.recognitionChanged.emit()

    def _set_recognition_error(self, code: str, message: str) -> None:
        self._recognition_state = "error"
        self._recognition_phase = ""
        self._recognition_error_text = message
        self.errorRequested.emit(message)
        self.recognitionChanged.emit()

    @Slot(object)
    def _on_recognition_finished(self, result: RecognitionResult) -> None:
        self._pending_recognition = result
        self._recognition_candidate_model.refresh(result.courses)
        self._recognition_state = "ready_to_import"
        self._recognition_phase = "识别完成，请确认后导入"
        self._recognition_error_text = ""
        self.recognitionChanged.emit()

    @Slot(object)
    def _on_recognition_failed(self, error: RecognitionError) -> None:
        messages = {
            "missing_api_key": "未设置 API Key。请先在设置中填写 OpenAI API Key。",
            "invalid_api_key": "API Key 无效或未授权。",
            "network": "网络连接失败，请检查网络后重试。",
            "timeout": "识别请求超时，请稍后重试。",
            "quota": "API 限额或额度不足。",
            "model_unavailable": "识别模型不可用，请检查模型配置。",
            "invalid_image": "图片格式无法读取或图片已损坏。",
            "output_parse": "模型输出无法解析，请重试或更换图片。",
            "api_error": "识别服务暂时不可用，请稍后重试。",
        }
        code = getattr(error, "code", "api_error")
        self._set_recognition_error(code, messages.get(code, "识别失败，请稍后重试。"))

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
        try:
            parse_custom_weeks(
                self._course_editor.customWeeksText,
                self._project.semester.total_weeks,
                required=self._course_editor.weekPattern == "custom",
            )
            course = self._course_editor.to_course(self._project.semester.total_weeks)
        except ValueError as exc:
            self.errorRequested.emit(f"课程无法保存：{exc}")
            return False
        issues = validate_project(
            ProjectDocument(
                schema_version=self._project.schema_version,
                project_name=self._project.project_name,
                school=self._project.school,
                campus=self._project.campus,
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
        if existing is not None and existing.recognition_status == "needs_review":
            course.needs_review_fields = []
            course.recognition_status = "confirmed"
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

    @Slot(str, str, int, result=bool)
    def updateSemester(self, name: str, first_week_monday: str, total_weeks: int) -> bool:
        if not self._project:
            self.errorRequested.emit("请先创建或打开一个项目。")
            return False
        name = str(name).strip()
        if not name:
            self.errorRequested.emit("学期名称不能为空。")
            return False
        try:
            monday = date.fromisoformat(str(first_week_monday).strip())
        except ValueError:
            self.errorRequested.emit("第一教学周周一必须是 YYYY-MM-DD 日期。")
            return False
        if monday.weekday() != 0:
            self.errorRequested.emit("第一教学周周一必须是周一。")
            return False
        try:
            total_weeks = int(total_weeks)
        except (TypeError, ValueError):
            self.errorRequested.emit("教学周数必须是整数。")
            return False
        if not 1 <= total_weeks <= 60:
            self.errorRequested.emit("教学周数应在 1 到 60 周之间。")
            return False
        over_limit = [
            course
            for course in self._project.courses
            if course.end_week > total_weeks or any(week > total_weeks for week in course.custom_weeks)
        ]
        if over_limit:
            names = "、".join(course.name for course in over_limit[:5])
            suffix = "等" if len(over_limit) > 5 else ""
            self.errorRequested.emit(
                f"有 {len(over_limit)} 门课程使用了第 {total_weeks + 1} 周之后的周次（{names}{suffix}）。"
                "请先调整课程周次，再修改学期总周数。"
            )
            return False
        candidate = deepcopy(self._project)
        candidate.semester.name = name
        candidate.semester.first_week_monday = monday.isoformat()
        candidate.semester.total_weeks = total_weeks
        issues = validate_project(candidate)
        if issues:
            self.errorRequested.emit("学期设置无法保存：" + "；".join(str(issue) for issue in issues))
            return False
        self._project.semester = candidate.semester
        self.projectChanged.emit()
        self._set_dirty(True)
        self.toastRequested.emit("学期设置已更新。")
        return True

    @Slot(result=bool)
    def addSection(self) -> bool:
        if not self._project:
            self.errorRequested.emit("请先创建或打开一个项目。")
            return False
        index = max((section.index for section in self._project.sections), default=0) + 1
        start_time, end_time = "08:00", "08:45"
        if self._project.sections:
            last = self._project.sections[-1]
            start_time = last.end_time
            try:
                end_value = datetime.strptime(start_time, "%H:%M") + timedelta(minutes=45)
                end_time = end_value.strftime("%H:%M")
                if end_time <= start_time:
                    start_time, end_time = "23:00", "23:45"
            except ValueError:
                start_time, end_time = "08:00", "08:45"
        section = Section(index=index, start_time=start_time, end_time=end_time, label=f"第{index}节")
        candidate = deepcopy(self._project)
        candidate.sections.append(section)
        issues = validate_project(candidate)
        if issues:
            self.errorRequested.emit("无法添加节次：" + "；".join(str(issue) for issue in issues))
            return False
        self._project.sections.append(section)
        self._section_model.append_section(section)
        self._set_dirty(True)
        self.toastRequested.emit(f"已添加第 {index} 节。")
        return True

    @Slot(int, result=bool)
    def deleteSection(self, section_index: int) -> bool:
        if not self._project:
            return False
        references = [
            course.name
            for course in self._project.courses
            if course.start_section <= section_index <= course.end_section
        ]
        if references:
            preview = "、".join(references[:3])
            suffix = "等" if len(references) > 3 else ""
            self.errorRequested.emit(
                f"无法删除第 {section_index} 节。当前仍有 {len(references)} 门课程使用该节次（{preview}{suffix}），请先调整这些课程。"
            )
            return False
        candidate = deepcopy(self._project)
        candidate.sections = [section for section in candidate.sections if section.index != section_index]
        issues = validate_project(candidate)
        if issues:
            self.errorRequested.emit("无法删除节次：" + "；".join(str(issue) for issue in issues))
            return False
        self._project.sections = candidate.sections
        self._section_model.remove_section(section_index)
        self._set_dirty(True)
        self.toastRequested.emit(f"已删除第 {section_index} 节。")
        return True

    @Slot(result=bool)
    def restoreDefaultSections(self) -> bool:
        if not self._project:
            return False
        default_sections = ProjectDocument.blank(self._project.project_name).sections
        candidate = deepcopy(self._project)
        candidate.sections = default_sections
        issues = validate_project(candidate)
        if issues:
            self.errorRequested.emit("无法恢复默认模板：请先调整使用超出默认模板范围的课程。")
            return False
        self._project.sections = default_sections
        self._section_model.refresh(default_sections)
        self._set_dirty(True)
        self.toastRequested.emit("已恢复默认节次模板。")
        return True

    def _selected_courses(self, course_ids: list) -> list[Course] | None:
        ids = [str(course_id) for course_id in course_ids]
        if not ids or len(ids) != len(set(ids)):
            self.errorRequested.emit("请先选择至少一门课程。")
            return None
        courses = [course for course in self._project.courses if course.id in ids]
        if len(courses) != len(ids):
            self.errorRequested.emit("所选课程已发生变化，请重新选择。")
            return None
        return courses

    def _replace_courses(self, courses: list[Course], message: str) -> bool:
        candidate = deepcopy(self._project)
        candidate.courses = list(courses)
        issues = validate_project(candidate)
        if issues:
            self.errorRequested.emit("批量操作无法应用：" + "；".join(str(issue) for issue in issues))
            return False
        self._project.courses = list(courses)
        self._course_model.refresh(self._project.courses)
        self._set_dirty(True)
        self.toastRequested.emit(message)
        return True

    @Slot("QVariantList", int, int, str, str, result=bool)
    def batchUpdateWeeks(self, course_ids: list, start_week: int, end_week: int, pattern: str, custom_text: str) -> bool:
        if not self._project:
            return False
        selected = self._selected_courses(course_ids)
        if selected is None:
            return False
        try:
            start_week, end_week = int(start_week), int(end_week)
            pattern = str(pattern)
            if pattern not in PATTERNS:
                raise ValueError("周次模式无效")
            if not 1 <= start_week <= end_week <= self._project.semester.total_weeks:
                raise ValueError(f"周次范围必须在 1 到 {self._project.semester.total_weeks} 周之间")
            custom_weeks = parse_custom_weeks(custom_text, self._project.semester.total_weeks, required=pattern == "custom")
        except ValueError as exc:
            self.errorRequested.emit(f"批量周次无法应用：{exc}")
            return False
        selected_ids = {course.id for course in selected}
        updated = [
            Course(**{
                **course.__dict__,
                "start_week": start_week if course.id in selected_ids else course.start_week,
                "end_week": end_week if course.id in selected_ids else course.end_week,
                "week_pattern": pattern if course.id in selected_ids else course.week_pattern,
                "custom_weeks": custom_weeks if course.id in selected_ids else course.custom_weeks,
            })
            for course in self._project.courses
        ]
        return self._replace_courses(updated, f"已修改 {len(selected)} 门课程的周次。")

    @Slot("QVariantList", str, str, str, result=bool)
    def batchUpdateLocation(self, course_ids: list, building: str, room: str, location_text: str) -> bool:
        if not self._project:
            return False
        selected = self._selected_courses(course_ids)
        if selected is None:
            return False
        selected_ids = {course.id for course in selected}
        updated = [
            Course(**{
                **course.__dict__,
                "building": str(building).strip() if course.id in selected_ids else course.building,
                "room": str(room).strip() if course.id in selected_ids else course.room,
                "location_text": str(location_text).strip() if course.id in selected_ids else course.location_text,
            })
            for course in self._project.courses
        ]
        return self._replace_courses(updated, f"已修改 {len(selected)} 门课程的地点。")

    @Slot("QVariantList", result=bool)
    def batchDeleteCourses(self, course_ids: list) -> bool:
        if not self._project:
            return False
        selected = self._selected_courses(course_ids)
        if selected is None:
            return False
        selected_ids = {course.id for course in selected}
        remaining = [course for course in self._project.courses if course.id not in selected_ids]
        return self._replace_courses(remaining, f"已删除 {len(selected)} 门课程。")

    @Slot(str)
    def notify(self, message: str) -> None:
        self.toastRequested.emit(message)

    def _set_project(self, project: ProjectDocument, path: str) -> None:
        self._project = project
        self._project_path = path
        self._course_model.refresh(project.courses)
        self._section_model.refresh(project.sections)
        self._course_editor.reset()
        self.clearImage()
        self.clearExcel()
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
