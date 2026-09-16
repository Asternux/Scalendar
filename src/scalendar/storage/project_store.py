"""UTF-8 JSON persistence for ``*.scalendar`` projects."""

from __future__ import annotations

import json
from pathlib import Path

from scalendar.core.models import ProjectDocument
from scalendar.core.validation import validate_project


class ProjectStore:
    """Read and write projects without coupling storage to the GUI."""

    encoding = "utf-8"

    def save(self, project: ProjectDocument, path: str | Path) -> Path:
        issues = validate_project(project)
        if issues:
            raise ValueError("项目无法保存：" + "；".join(str(issue) for issue in issues))
        project.touch()
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(json.dumps(project.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding=self.encoding)
        temporary.replace(target)
        return target

    def load(self, path: str | Path) -> ProjectDocument:
        source = Path(path)
        data = json.loads(source.read_text(encoding=self.encoding))
        project = ProjectDocument.from_dict(data)
        issues = validate_project(project)
        if issues:
            raise ValueError("项目无法打开：" + "；".join(str(issue) for issue in issues))
        return project


def save_project(project: ProjectDocument, path: str | Path) -> Path:
    return ProjectStore().save(project, path)


def load_project(path: str | Path) -> ProjectDocument:
    return ProjectStore().load(path)
