from pathlib import Path

from scalendar.core.models import Course, ProjectDocument
from scalendar.storage.project_store import ProjectStore


def test_project_store_writes_utf8_json_and_reopens(tmp_path: Path):
    project = ProjectDocument.blank("中文学期")
    project.courses.append(Course(id="stable-id", name="人工智能导论", start_section=1, end_section=2))
    path = tmp_path / "semester.scalendar"
    store = ProjectStore()
    saved = store.save(project, path)
    loaded = store.load(saved)
    assert saved == path
    assert "人工智能导论" in path.read_text(encoding="utf-8")
    assert loaded.project_name == "中文学期"
    assert loaded.courses[0].id == "stable-id"
