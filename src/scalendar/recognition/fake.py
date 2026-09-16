"""Deterministic provider used by tests and local UI smoke checks."""

from __future__ import annotations

from pathlib import Path

from .base import RecognitionContext, RecognitionError, RecognitionProvider
from .models import RecognitionResult


class FakeRecognitionProvider(RecognitionProvider):
    def __init__(self, result: RecognitionResult | None = None, error: RecognitionError | None = None) -> None:
        self.result = result or RecognitionResult()
        self.error = error
        self.calls: list[tuple[Path, RecognitionContext]] = []

    def recognize(self, image: Path, context: RecognitionContext) -> RecognitionResult:
        self.calls.append((image, context))
        if self.error is not None:
            raise self.error
        return self.result
