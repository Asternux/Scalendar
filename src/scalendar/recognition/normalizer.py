"""Conservative normalization and validation for recognition payloads."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from scalendar.core.models import Course
from scalendar.core.validation import PATTERNS, parse_custom_weeks

from .base import RecognitionContext
from .models import CandidateCourse, RecognitionIssue, RecognitionResult


_WEEKDAY_NAMES = {
    "周一": 1, "星期一": 1, "礼拜一": 1,
    "周二": 2, "星期二": 2, "礼拜二": 2,
    "周三": 3, "星期三": 3, "礼拜三": 3,
    "周四": 4, "星期四": 4, "礼拜四": 4,
    "周五": 5, "星期五": 5, "礼拜五": 5,
    "周六": 6, "星期六": 6, "礼拜六": 6,
    "周日": 7, "星期日": 7, "星期天": 7, "周天": 7,
}

_PATTERN_ALIASES = {
    "每周": "all", "全周": "all", "all": "all",
    "单周": "odd", "odd": "odd",
    "双周": "even", "even": "even",
    "自定义": "custom", "custom": "custom",
}


def _optional_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    return int(text) if text.isdigit() else None


def _weekday(value: Any) -> int | None:
    if isinstance(value, str):
        text = value.strip()
        if text in _WEEKDAY_NAMES:
            return _WEEKDAY_NAMES[text]
    return _optional_int(value)


def _pattern(value: Any) -> str | None:
    return _PATTERN_ALIASES.get(str(value or "").strip().lower())


def _custom_weeks(value: Any, total_weeks: int) -> tuple[list[int], str | None]:
    text = ",".join(str(item) for item in value) if isinstance(value, list) else str(value or "")
    try:
        return parse_custom_weeks(text, total_weeks, required=bool(text.strip())), None
    except ValueError as exc:
        return [], str(exc)


def _field_or_review(raw: Mapping[str, Any], field: str, review: set[str]) -> int | None:
    value = _optional_int(raw.get(field))
    if value is None:
        review.add(field)
    return value


def normalize_recognition_payload(payload: Any, context: RecognitionContext) -> RecognitionResult:
    """Normalize a structured provider payload without guessing facts."""

    raw_courses = payload.get("courses", []) if isinstance(payload, Mapping) else payload
    if not isinstance(raw_courses, list):
        return RecognitionResult(
            issues=[RecognitionIssue("invalid_payload", "识别结果不是课程列表。", severity="error")]
        )

    result = RecognitionResult()
    seen: set[tuple[Any, ...]] = set()
    valid_sections = set(context.section_indices)
    max_section = max(valid_sections, default=0)

    for position, raw in enumerate(raw_courses):
        if not isinstance(raw, Mapping):
            result.issues.append(RecognitionIssue("invalid_course", f"第 {position + 1} 条课程不是对象。", severity="error"))
            continue
        name = str(raw.get("name") or "").strip()
        if not name:
            result.issues.append(RecognitionIssue("missing_name", f"第 {position + 1} 条课程缺少课程名称。", field="name", severity="error"))
            continue
        raw_review = raw.get("needs_review_fields", [])
        review = {str(item) for item in raw_review if str(item).strip()} if isinstance(raw_review, list) else set()

        weekday = _weekday(raw.get("weekday"))
        if weekday is None or not 1 <= weekday <= 7:
            review.add("weekday")
            weekday = None

        start_section = _field_or_review(raw, "start_section", review)
        end_section = _field_or_review(raw, "end_section", review)
        if valid_sections:
            if start_section not in valid_sections:
                review.add("start_section")
                start_section = None
            if end_section not in valid_sections:
                review.add("end_section")
                end_section = None
        if max_section and any(section is not None and section > max_section for section in (start_section, end_section)):
            review.update({"start_section", "end_section"})
            start_section = end_section = None
        if start_section is not None and end_section is not None and start_section > end_section:
            review.update({"start_section", "end_section"})
            start_section = end_section = None

        start_week = _field_or_review(raw, "start_week", review)
        end_week = _field_or_review(raw, "end_week", review)
        for field_name, value in (("start_week", start_week), ("end_week", end_week)):
            if value is not None and not 1 <= value <= context.total_weeks:
                review.add(field_name)
        if start_week is not None and not 1 <= start_week <= context.total_weeks:
            start_week = None
        if end_week is not None and not 1 <= end_week <= context.total_weeks:
            end_week = None
        if start_week is not None and end_week is not None and start_week > end_week:
            review.update({"start_week", "end_week"})
            start_week = end_week = None

        pattern = _pattern(raw.get("week_pattern"))
        if pattern is None:
            pattern = "all"
            review.add("week_pattern")
        custom_weeks: list[int] = []
        if pattern == "custom":
            custom_weeks, custom_error = _custom_weeks(raw.get("custom_weeks"), context.total_weeks)
            if custom_error:
                review.add("custom_weeks")
                result.issues.append(RecognitionIssue("invalid_custom_weeks", custom_error, field="custom_weeks"))
                pattern = "all"

        candidate = CandidateCourse(
            name=name,
            weekday=weekday,
            start_section=start_section,
            end_section=end_section,
            start_week=start_week,
            end_week=end_week,
            week_pattern=pattern,
            custom_weeks=custom_weeks,
            teacher=str(raw.get("teacher") or "").strip(),
            building=str(raw.get("building") or "").strip(),
            room=str(raw.get("room") or "").strip(),
            location_text=str(raw.get("location_text") or "").strip(),
            needs_review_fields=sorted(review),
            notes=str(raw.get("notes") or "").strip(),
        )
        key = (
            candidate.name, candidate.weekday, candidate.start_section,
            candidate.end_section, candidate.start_week, candidate.end_week,
            candidate.week_pattern, tuple(candidate.custom_weeks),
        )
        if key in seen:
            result.issues.append(RecognitionIssue("duplicate_course", f"已忽略重复课程“{name}”。", field="name"))
            continue
        seen.add(key)
        result.courses.append(candidate)

    if not result.courses:
        result.issues.append(RecognitionIssue("no_courses", "识别结果没有可用课程。", severity="error"))
    return result


def candidate_to_course(candidate: CandidateCourse, total_weeks: int, section_indices: tuple[int, ...]) -> Course:
    """Create an explicitly review-marked Core Course from a candidate.

    Missing numeric values receive editable placeholders only at the import
    boundary. They are never presented as recognized facts.
    """

    first_section = min(section_indices, default=1)
    last_section = max(section_indices, default=first_section)
    start_section = min(max(first_section, candidate.start_section or first_section), last_section)
    end_section = min(max(start_section, candidate.end_section or start_section), last_section)
    start_week = min(max(1, candidate.start_week or 1), total_weeks)
    end_week = min(max(start_week, candidate.end_week or total_weeks), total_weeks)
    pattern = candidate.week_pattern if candidate.week_pattern in PATTERNS else "all"
    custom_weeks = list(candidate.custom_weeks) if pattern == "custom" else []
    review_fields = list(candidate.needs_review_fields)
    notes = candidate.notes
    if review_fields:
        review_note = "AI 未确认字段：" + "、".join(review_fields)
        notes = f"{notes}；{review_note}" if notes else review_note
    return Course(
        name=candidate.name,
        weekday=candidate.weekday or 1,
        start_section=start_section,
        end_section=end_section,
        start_week=start_week,
        end_week=end_week,
        week_pattern=pattern,
        custom_weeks=custom_weeks,
        teacher=candidate.teacher,
        building=candidate.building,
        room=candidate.room,
        location_text=candidate.location_text,
        notes=notes,
        recognition_status="needs_review" if review_fields else "recognized",
        needs_review_fields=review_fields,
    )
