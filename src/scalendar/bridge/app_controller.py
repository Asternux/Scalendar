"""Small QML-facing controller for the M2 shell."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot


class AppController(QObject):
    pageRequested = Signal(str)
    courseRequested = Signal("QVariant")
    toastRequested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._project_name = "2026 秋季学期 · 我的课表"
        self._demo_courses = [
            {"id": "demo-math", "name": "高等数学", "meta": "周一 · 第 1–2 节", "teacher": "李老师", "location": "理科楼 A101", "color": "#5B8DEF"},
            {"id": "demo-english", "name": "大学英语", "meta": "周二 · 第 3–4 节", "teacher": "王老师", "location": "外语楼 204", "color": "#63B7A6"},
            {"id": "demo-design", "name": "交互设计基础", "meta": "周三 · 第 5–6 节", "teacher": "陈老师", "location": "艺术中心 302", "color": "#E5A458"},
            {"id": "demo-physics", "name": "大学物理", "meta": "周四 · 第 1–2 节", "teacher": "周老师", "location": "实验楼 B206", "color": "#B47ED8"},
            {"id": "demo-lab", "name": "程序设计实验", "meta": "周五 · 第 7–8 节", "teacher": "赵老师", "location": "计算机楼 401", "color": "#E87878"},
            {"id": "demo-seminar", "name": "学术写作研讨", "meta": "周六 · 第 3–4 节", "teacher": "刘老师", "location": "图书馆研讨室", "color": "#6FB2D4"},
        ]

    @Property(str, constant=True)
    def projectName(self) -> str:
        return self._project_name

    @Property("QVariantList", constant=True)
    def demoCourses(self) -> list[dict[str, str]]:
        return self._demo_courses

    @Slot(str)
    def navigate(self, page: str) -> None:
        self.pageRequested.emit(page)

    @Slot("QVariant")
    def editCourse(self, course: object) -> None:
        self.courseRequested.emit(course)

    @Slot(str)
    def notify(self, message: str) -> None:
        self.toastRequested.emit(message)
