"""Pluggable timetable image recognition adapters."""

from .base import RecognitionContext, RecognitionError, RecognitionProvider
from .models import CandidateCourse, RecognitionIssue, RecognitionResult

__all__ = [
    "CandidateCourse",
    "RecognitionContext",
    "RecognitionError",
    "RecognitionIssue",
    "RecognitionProvider",
    "RecognitionResult",
]
