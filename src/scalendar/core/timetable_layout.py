"""Central timetable geometry tokens shared by the timetable view."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimetableLayoutSpec:
    """Geometry constants for one compact, readable weekly grid.

    QML owns the available width; this object owns the timetable-specific
    tokens so row/column calculations do not drift between components.
    """

    time_column_width: int = 82
    day_header_height: int = 42
    section_height: int = 76
    cell_gap: int = 4


DEFAULT_TIMETABLE_LAYOUT = TimetableLayoutSpec()
