"""Provider-neutral recognition DTOs.

These DTOs intentionally permit unknown numeric fields. A candidate is not a
Core Course until the user confirms the recognition result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class RecognitionIssue:
    code: str
    message: str
    field: str = ""
    severity: str = "warning"


@dataclass
class CandidateCourse:
    name: str
    weekday: Optional[int] = None
    start_section: Optional[int] = None
    end_section: Optional[int] = None
    start_week: Optional[int] = None
    end_week: Optional[int] = None
    week_pattern: str = "all"
    custom_weeks: list[int] = field(default_factory=list)
    teacher: str = ""
    building: str = ""
    room: str = ""
    location_text: str = ""
    needs_review_fields: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def needs_review(self) -> bool:
        return bool(self.needs_review_fields)


@dataclass
class RecognitionResult:
    courses: list[CandidateCourse] = field(default_factory=list)
    issues: list[RecognitionIssue] = field(default_factory=list)
    provider: str = ""

    @property
    def review_count(self) -> int:
        return sum(1 for course in self.courses if course.needs_review)
