"""Provider boundary for timetable image recognition.

Providers know about images and remote/local recognition services. They do not
know about Qt, QML, or the active project instance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from .models import RecognitionResult


@dataclass(frozen=True)
class RecognitionContext:
    school: str = ""
    campus: str = ""
    total_weeks: int = 20
    section_indices: tuple[int, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "school": self.school,
            "campus": self.campus,
            "total_weeks": self.total_weeks,
            "section_indices": list(self.section_indices),
        }


class RecognitionError(RuntimeError):
    """A safe, user-facing category for a recognition failure.

    The optional detail must never contain credentials. The controller maps
    code to Chinese UI text.
    """

    def __init__(self, code: str, message: str = "", detail: str = "") -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message or code
        self.detail = detail


class RecognitionProvider(ABC):
    requires_api_key = False

    @abstractmethod
    def recognize(self, image: Path, context: RecognitionContext) -> RecognitionResult:
        """Return structured candidates for one image."""
