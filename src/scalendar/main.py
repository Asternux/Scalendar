"""Scalendar desktop entry point."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtQml import QQmlApplicationEngine

from scalendar.bridge.app_controller import AppController


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Scalendar V1 desktop shell")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    args = parser.parse_args(argv)
    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv if argv is None else [sys.argv[0], *argv])
    app.setApplicationName("Scalendar")
    app.setOrganizationName("Scalendar")
    engine = QQmlApplicationEngine()
    controller = AppController()
    engine.rootContext().setContextProperty("appController", controller)
    engine.rootContext().setContextProperty("courseEditor", controller.courseEditor)
    engine.rootContext().setContextProperty("initialWidth", max(args.width, 1120))
    engine.rootContext().setContextProperty("initialHeight", max(args.height, 720))
    engine.rootContext().setContextProperty("initialCourseId", "")
    qml_dir = Path(__file__).parent / "ui"
    engine.addImportPath(str(qml_dir))
    qml_path = qml_dir / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
