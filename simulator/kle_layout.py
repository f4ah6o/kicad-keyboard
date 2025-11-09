"""Utilities for loading Keyboard Layout Editor (KLE) JSON layouts."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

KLE_UNIT_MM = 19.05


def _default_state():
    return {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}


@dataclass
class KLEKey:
    label: str
    row_index: int
    x_units: float  # left edge in units
    y_units: float  # top edge in units
    width_units: float
    height_units: float

    @property
    def x_mm(self) -> float:
        return self.x_units * KLE_UNIT_MM

    @property
    def y_mm(self) -> float:
        return self.y_units * KLE_UNIT_MM

    @property
    def width_mm(self) -> float:
        return self.width_units * KLE_UNIT_MM

    @property
    def height_mm(self) -> float:
        return self.height_units * KLE_UNIT_MM

    @property
    def center_x_mm(self) -> float:
        return (self.x_units + self.width_units / 2.0) * KLE_UNIT_MM

    @property
    def center_y_mm(self) -> float:
        return (self.y_units + self.height_units / 2.0) * KLE_UNIT_MM


@dataclass
class KLELayout:
    rows: List[List[KLEKey]]

    @property
    def flat(self) -> List[KLEKey]:
        result: List[KLEKey] = []
        for row in self.rows:
            result.extend(row)
        return result


def load_kle_layout(path: str | Path) -> KLELayout:
    """Load a KLE JSON file from disk."""
    data = json.loads(Path(path).read_text())
    return parse_kle_layout(data)


def parse_kle_layout(layout_data: Sequence[Sequence]) -> KLELayout:
    rows: List[List[KLEKey]] = []

    for row_index, row in enumerate(layout_data):
        x_cursor = 0.0
        state = _default_state()
        row_keys: List[KLEKey] = []

        for item in row:
            if isinstance(item, dict):
                state.update(item)
                continue

            x_cursor += state.get("x", 0.0)
            y_units = row_index + state.get("y", 0.0)
            width = state.get("w", 1.0)
            height = state.get("h", 1.0)

            row_keys.append(
                KLEKey(
                    label=str(item),
                    row_index=row_index,
                    x_units=x_cursor,
                    y_units=y_units,
                    width_units=width,
                    height_units=height,
                )
            )

            x_cursor += width
            state = _default_state()

        # Align left edges for rows 0-2 to ensure consistent staggering
        if row_index in (0, 1, 2) and row_keys:
            min_left = min(key.x_units for key in row_keys)
            for key in row_keys:
                key.x_units -= min_left

        rows.append(row_keys)

    return KLELayout(rows=rows)


def apply_kle_layout(simulator, kle_layout: KLELayout):
    """Map a KLE layout onto the simulator's footprints for initial placement."""
    rows_to_use = min(simulator.rows, len(kle_layout.rows))

    for r in range(rows_to_use):
        row_keys = kle_layout.rows[r]
        cols_to_use = min(len(simulator.footprints[r]), len(row_keys))

        for c in range(cols_to_use):
            key = row_keys[c]
            fp = simulator.footprints[r][c]
            fp.move_to(key.center_x_mm, key.center_y_mm)
            fp.width = key.width_mm
            fp.height = key.height_mm
            fp.rotate_to(0.0)
