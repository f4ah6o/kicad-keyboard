"""Tests for kle_layout module."""
import pytest
import json
from pathlib import Path
from kle_layout import (
    KLEKey,
    KLELayout,
    parse_kle_layout,
    load_kle_layout,
    apply_kle_layout,
    KLE_UNIT_MM,
)
from grin_simulator import GrinSimulator


class TestKLEKey:
    """Test KLEKey dataclass."""

    def test_kle_key_creation(self):
        """Test creating a KLE key."""
        key = KLEKey(
            label="A",
            row_index=0,
            x_units=0.0,
            y_units=0.0,
            width_units=1.0,
            height_units=1.0
        )
        assert key.label == "A"
        assert key.row_index == 0

    def test_kle_key_mm_conversion(self):
        """Test unit to mm conversion."""
        key = KLEKey(
            label="A",
            row_index=0,
            x_units=1.0,
            y_units=2.0,
            width_units=1.5,
            height_units=1.0
        )
        assert key.x_mm == 1.0 * KLE_UNIT_MM
        assert key.y_mm == 2.0 * KLE_UNIT_MM
        assert key.width_mm == 1.5 * KLE_UNIT_MM
        assert key.height_mm == 1.0 * KLE_UNIT_MM

    def test_kle_key_center(self):
        """Test center calculation."""
        key = KLEKey(
            label="A",
            row_index=0,
            x_units=0.0,
            y_units=0.0,
            width_units=2.0,
            height_units=2.0
        )
        # Center should be at (1.0, 1.0) in units
        assert key.center_x_mm == 1.0 * KLE_UNIT_MM
        assert key.center_y_mm == 1.0 * KLE_UNIT_MM


class TestKLELayout:
    """Test KLELayout class."""

    def test_kle_layout_flat(self):
        """Test flattening layout rows."""
        key1 = KLEKey("A", 0, 0.0, 0.0, 1.0, 1.0)
        key2 = KLEKey("B", 0, 1.0, 0.0, 1.0, 1.0)
        key3 = KLEKey("C", 1, 0.0, 1.0, 1.0, 1.0)

        layout = KLELayout(rows=[[key1, key2], [key3]])
        flat = layout.flat

        assert len(flat) == 3
        assert flat[0] == key1
        assert flat[1] == key2
        assert flat[2] == key3


class TestParseKLELayout:
    """Test KLE layout parsing."""

    def test_parse_simple_layout(self):
        """Test parsing a simple 2x2 layout."""
        data = [
            ["Q", "W"],
            ["A", "S"]
        ]

        layout = parse_kle_layout(data)

        assert len(layout.rows) == 2
        assert len(layout.rows[0]) == 2
        assert len(layout.rows[1]) == 2
        assert layout.rows[0][0].label == "Q"
        assert layout.rows[1][1].label == "S"

    def test_parse_layout_with_width(self):
        """Test parsing layout with custom key width."""
        data = [
            [{"w": 2.0}, "Tab", "Q"],
        ]

        layout = parse_kle_layout(data)

        assert len(layout.rows) == 1
        assert len(layout.rows[0]) == 2
        assert layout.rows[0][0].label == "Tab"
        assert layout.rows[0][0].width_units == 2.0

    def test_parse_layout_with_spacing(self):
        """Test parsing layout with x spacing."""
        data = [
            ["A", {"x": 0.5}, "B"],
        ]

        layout = parse_kle_layout(data)

        assert len(layout.rows[0]) == 2
        # Second key should be offset by 1.0 (key width) + 0.5 (spacing)
        assert layout.rows[0][1].x_units > layout.rows[0][0].x_units + 1.0


class TestApplyKLELayout:
    """Test applying KLE layout to simulator."""

    def test_apply_kle_layout(self):
        """Test applying KLE layout to simulator footprints."""
        # Create a simple layout
        data = [
            ["A", "B", "C"],
            ["D", "E", "F"]
        ]
        kle_layout = parse_kle_layout(data)

        # Create simulator with matching dimensions
        sim = GrinSimulator(rows=2, cols=3)

        # Apply layout
        apply_kle_layout(sim, kle_layout)

        # Check that footprints were positioned
        # First key should be at its center position
        fp00 = sim.footprints[0][0]
        assert fp00.x > 0  # Should be positioned, not at origin
        assert fp00.rotation == 0.0  # Should have no rotation

    def test_apply_kle_layout_different_sizes(self):
        """Test applying KLE layout with size mismatch."""
        # KLE layout larger than simulator
        data = [
            ["A", "B", "C", "D", "E"],
        ]
        kle_layout = parse_kle_layout(data)

        # Smaller simulator
        sim = GrinSimulator(rows=1, cols=3)

        # Should apply without error, using min(kle, sim) keys
        apply_kle_layout(sim, kle_layout)

        # All 3 simulator keys should be positioned
        for fp in sim.footprints[0]:
            assert fp.x > 0


class TestLoadKLELayout:
    """Test loading KLE layout from file."""

    def test_load_kle_layout_file(self, tmp_path):
        """Test loading KLE layout from JSON file."""
        # Create temporary KLE JSON file
        kle_data = [
            ["A", "B"],
            ["C", "D"]
        ]
        kle_file = tmp_path / "test_layout.json"
        kle_file.write_text(json.dumps(kle_data))

        # Load the file
        layout = load_kle_layout(kle_file)

        assert len(layout.rows) == 2
        assert len(layout.rows[0]) == 2
        assert layout.rows[0][0].label == "A"
