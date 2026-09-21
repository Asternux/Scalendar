import json
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QImage

from scalendar.bridge.app_controller import AppController
from scalendar.bridge.qt_models import CourseListModel
from scalendar.core.models import ProjectDocument
from scalendar.recognition.base import RecognitionContext, RecognitionError
from scalendar.recognition.fake import FakeRecognitionProvider
from scalendar.recognition.models import CandidateCourse, RecognitionResult
from scalendar.recognition.normalizer import candidate_to_course, normalize_recognition_payload
from scalendar.recognition.openai_vision import OpenAIVisionProvider


@pytest.fixture(scope="module")
def qapp():
    app = QCoreApplication.instance() or QCoreApplication([])
    yield app


def context() -> RecognitionContext:
    return RecognitionContext(school="南京大学", campus="仙林", total_weeks=16, section_indices=tuple(range(1, 13)))


def make_image(path: Path) -> Path:
    image = QImage(64, 48, QImage.Format.Format_RGB32)
    image.fill(0xFFE8EEF9)
    assert image.save(str(path), "PNG")
    return path


def wait_for_recognition(controller: AppController, qapp, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while controller.recognitionState == "recognizing" and time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.01)
    qapp.processEvents()
    assert controller.recognitionState != "recognizing"


def test_project_context_and_old_schema_one_compatibility():
    project = ProjectDocument.blank("2026 秋季学期")
    project.school = "南京大学"
    project.campus = "仙林"
    restored = ProjectDocument.from_dict(project.to_dict())
    assert restored.school == "南京大学"
    assert restored.campus == "仙林"
    assert restored.schema_version == 1

    old_data = project.to_dict()
    old_data["project"].pop("school")
    old_data["project"].pop("campus")
    old_restored = ProjectDocument.from_dict(old_data)
    assert old_restored.school == ""
    assert old_restored.campus == ""


def test_normalizer_preserves_week_patterns_and_deduplicates_exact_courses():
    result = normalize_recognition_payload(
        {
            "courses": [
                {
                    "name": "高等数学",
                    "weekday": "周一",
                    "start_section": 1,
                    "end_section": 2,
                    "start_week": 1,
                    "end_week": 16,
                    "week_pattern": "每周",
                    "custom_weeks": [],
                    "teacher": "李老师",
                    "building": "二教",
                    "room": "301",
                    "location_text": "二教301",
                    "needs_review_fields": [],
                    "notes": "",
                },
                {
                    "name": "英语",
                    "weekday": 3,
                    "start_section": 3,
                    "end_section": 4,
                    "start_week": 1,
                    "end_week": 16,
                    "week_pattern": "单周",
                    "custom_weeks": [],
                    "teacher": "",
                    "building": "",
                    "room": "",
                    "location_text": "一教201",
                    "needs_review_fields": [],
                    "notes": "",
                },
                {
                    "name": "体育",
                    "weekday": 5,
                    "start_section": 5,
                    "end_section": 6,
                    "start_week": 1,
                    "end_week": 16,
                    "week_pattern": "custom",
                    "custom_weeks": [1, 4, 8, 12],
                    "teacher": "",
                    "building": "",
                    "room": "",
                    "location_text": "体育馆",
                    "needs_review_fields": [],
                    "notes": "",
                },
                {
                    "name": "高等数学",
                    "weekday": "周一",
                    "start_section": 1,
                    "end_section": 2,
                    "start_week": 1,
                    "end_week": 16,
                    "week_pattern": "all",
                    "custom_weeks": [],
                    "teacher": "李老师",
                    "building": "二教",
                    "room": "301",
                    "location_text": "二教301",
                    "needs_review_fields": [],
                    "notes": "",
                },
            ]
        },
        context(),
    )

    assert [course.name for course in result.courses] == ["高等数学", "英语", "体育"]
    assert [course.week_pattern for course in result.courses] == ["all", "odd", "custom"]
    assert result.courses[0].weekday == 1
    assert result.courses[2].custom_weeks == [1, 4, 8, 12]
    assert any(issue.code == "duplicate_course" for issue in result.issues)


def test_normalizer_marks_unknown_numeric_fields_without_guessing():
    result = normalize_recognition_payload(
        {"courses": [{"name": "待确认课程", "weekday": None, "start_section": None, "end_section": None, "start_week": None, "end_week": None, "week_pattern": "all", "custom_weeks": []}]},
        context(),
    )
    candidate = result.courses[0]
    assert candidate.weekday is None
    assert candidate.start_section is None
    assert candidate.end_section is None
    assert candidate.start_week is None
    assert candidate.end_week is None
    assert set(candidate.needs_review_fields) >= {"weekday", "start_section", "end_section", "start_week", "end_week"}

    course = candidate_to_course(candidate, 16, tuple(range(1, 13)))
    assert course.recognition_status == "needs_review"
    assert course.needs_review_fields == sorted(course.needs_review_fields)
    assert "AI 未确认字段" in course.notes


def test_normalizer_rejects_invalid_ranges_and_custom_weeks():
    result = normalize_recognition_payload(
        {
            "courses": [
                {"name": "错位", "weekday": 8, "start_section": 12, "end_section": 1, "start_week": 0, "end_week": 17, "week_pattern": "all", "custom_weeks": []},
                {"name": "自定义错误", "weekday": 2, "start_section": 1, "end_section": 1, "start_week": 1, "end_week": 16, "week_pattern": "custom", "custom_weeks": [1, 99]},
            ]
        },
        context(),
    )
    assert set(result.courses[0].needs_review_fields) >= {"weekday", "start_section", "end_section", "start_week", "end_week"}
    assert "custom_weeks" in result.courses[1].needs_review_fields
    assert any(issue.code == "invalid_custom_weeks" for issue in result.issues)


class FakeResponse:
    def __init__(self, output_text: str):
        self.output_text = output_text


class FakeResponses:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response: FakeResponse):
        self.responses = FakeResponses(response)


def test_openai_provider_uses_image_input_and_strict_structured_output(tmp_path: Path):
    image_path = make_image(tmp_path / "table.png")
    payload = {"courses": [{"name": "高等数学", "weekday": 1, "start_section": 1, "end_section": 2, "start_week": 1, "end_week": 16, "week_pattern": "all", "custom_weeks": [], "teacher": "", "building": "", "room": "", "location_text": "二教301", "needs_review_fields": [], "notes": ""}]}
    fake_client = FakeClient(FakeResponse(json.dumps(payload, ensure_ascii=False)))
    provider = OpenAIVisionProvider(api_key="secret-not-in-request", model="test-model", client=fake_client)

    result = provider.recognize(image_path, context())

    assert result.provider == "openai"
    assert result.courses[0].name == "高等数学"
    request = fake_client.responses.calls[0]
    assert request["model"] == "test-model"
    assert request["input"][0]["content"][1]["type"] == "input_image"
    assert request["input"][0]["content"][1]["image_url"].startswith("data:image/png;base64,")
    assert request["text"]["format"]["type"] == "json_schema"
    assert request["text"]["format"]["strict"] is True
    assert "secret-not-in-request" not in json.dumps(request)


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (type("AuthenticationError", (Exception,), {})(), "invalid_api_key"),
        (type("RateLimitError", (Exception,), {})(), "quota"),
        (TimeoutError("late"), "timeout"),
        (ConnectionError("offline"), "network"),
    ],
)
def test_openai_provider_maps_common_api_errors(error, code):
    assert OpenAIVisionProvider._map_api_error(error).code == code


def test_fake_provider_records_context_and_controller_import_roundtrip(qapp, tmp_path: Path):
    candidate = CandidateCourse(
        name="高等数学",
        weekday=1,
        start_section=1,
        end_section=2,
        start_week=1,
        end_week=16,
        location_text="二教301",
    )
    provider = FakeRecognitionProvider(RecognitionResult([candidate], provider="fake"))
    controller = AppController(provider)
    assert controller.createProject("我的课表", "2026 秋季学期", "2026-09-07", 16)
    assert controller.updateProjectContext("南京大学", "仙林")
    image_path = make_image(tmp_path / "semester.png")
    assert controller.selectImage(str(image_path))
    assert controller.startRecognition()
    wait_for_recognition(controller, qapp)

    assert controller.recognitionState == "ready_to_import"
    assert controller.recognitionCourseCount == 1
    assert controller.recognitionReviewCount == 0
    assert provider.calls[0][1].school == "南京大学"
    assert provider.calls[0][1].campus == "仙林"
    assert provider.calls[0][1].section_indices == tuple(range(1, 13))

    assert controller.applyRecognitionResult()
    assert controller.courseModel.rowCount() == 1
    course_id = controller.courseModel.data(controller.courseModel.index(0, 0), CourseListModel.CourseIdRole)
    project_path = tmp_path / "roundtrip.scalendar"
    assert controller.saveAs(str(project_path))
    reopened = AppController(FakeRecognitionProvider())
    assert reopened.openProject(str(project_path))
    assert reopened.school == "南京大学"
    assert reopened.campus == "仙林"
    assert reopened.courseModel.data(reopened.courseModel.index(0, 0), CourseListModel.CourseIdRole) == course_id
    assert reopened.courseModel.data(reopened.courseModel.index(0, 0), CourseListModel.NameRole) == "高等数学"


def test_controller_keeps_needs_review_visible_after_import(qapp, tmp_path: Path):
    candidate = CandidateCourse(name="待确认课程", location_text="待确认", needs_review_fields=["weekday", "start_section"])
    controller = AppController(FakeRecognitionProvider(RecognitionResult([candidate])))
    assert controller.createProject("项目", "学期", "2026-09-07", 16)
    assert controller.selectImage(str(make_image(tmp_path / "review.jpg"))) is True
    assert controller.startRecognition() is True
    wait_for_recognition(controller, qapp)
    assert controller.recognitionReviewCount == 1
    assert controller.applyRecognitionResult() is True
    course = controller.courseModel.course_at(controller.courseModel.data(controller.courseModel.index(0, 0), CourseListModel.CourseIdRole))
    assert course is not None
    assert course.recognition_status == "needs_review"
    assert course.needs_review_fields == ["weekday", "start_section"]


def test_controller_maps_provider_error_and_does_not_persist_api_key(qapp, tmp_path: Path):
    provider = FakeRecognitionProvider(error=RecognitionError("network", "offline"))
    controller = AppController(provider)
    assert controller.createProject("项目", "学期", "2026-09-07", 16)
    assert controller.selectImage(str(make_image(tmp_path / "error.webp")))
    assert controller.setApiKey("secret-only-in-memory")
    assert controller.startRecognition()
    wait_for_recognition(controller, qapp)
    assert controller.recognitionState == "error"
    assert "网络连接失败" in controller.recognitionErrorText
    project_path = tmp_path / "no-secret.scalendar"
    assert controller.saveAs(str(project_path))
    assert "secret-only-in-memory" not in project_path.read_text(encoding="utf-8")


def test_controller_missing_api_key_fails_before_worker(qapp, tmp_path: Path):
    controller = AppController(OpenAIVisionProvider(api_key=""))
    assert controller.createProject("项目", "学期", "2026-09-07", 16)
    assert controller.selectImage(str(make_image(tmp_path / "missing-key.png")))
    assert controller.startRecognition() is False
    assert controller.recognitionState == "error"
    assert "未设置 API Key" in controller.recognitionErrorText
