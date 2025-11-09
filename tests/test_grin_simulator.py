"""Tests for grin_simulator module."""
import pytest
import numpy as np
from grin_simulator import GrinSimulator, SectionType, Section


class TestSection:
    """Test Section dataclass."""

    def test_section_creation(self):
        """Test creating a section."""
        sec = Section(type=SectionType.HORIZONTAL, cols=[0, 1, 2])
        assert sec.type == SectionType.HORIZONTAL
        assert sec.cols == [0, 1, 2]
        assert sec.theta0 == 0.0


class TestGrinSimulator:
    """Test GrinSimulator class."""

    def test_simulator_creation_basic(self):
        """Test basic simulator creation."""
        sim = GrinSimulator(rows=3, cols=5)
        assert sim.rows == 3
        assert sim.cols == 5
        assert len(sim.footprints) == 3
        assert len(sim.footprints[0]) == 5

    def test_simulator_creation_with_params(self):
        """Test simulator creation with custom parameters."""
        sim = GrinSimulator(
            rows=2,
            cols=7,
            center=(150.0, 150.0),
            base_radius=120.0,
            radius_step=15.0,
            base_pitch=20.0
        )
        assert sim.rows == 2
        assert sim.cols == 7
        assert sim.center == (150.0, 150.0)
        assert sim.base_radius == 120.0
        assert sim.radius_step == 15.0
        assert sim.base_pitch == 20.0

    def test_simulator_radius_calculation(self):
        """Test that radii decrease properly per row."""
        sim = GrinSimulator(rows=3, cols=5, base_radius=100.0, radius_step=10.0)
        assert sim.R[0] == 100.0  # Top row
        assert sim.R[1] == 90.0   # Middle row
        assert sim.R[2] == 80.0   # Bottom row

    def test_simulator_with_cols_per_row(self):
        """Test simulator with different column counts per row."""
        cols_per_row = [5, 7, 3]
        sim = GrinSimulator(rows=3, cols_per_row=cols_per_row)

        assert sim.rows == 3
        assert sim.cols_per_row == cols_per_row
        assert len(sim.footprints[0]) == 5
        assert len(sim.footprints[1]) == 7
        assert len(sim.footprints[2]) == 3

    def test_simulator_cols_per_row_mismatch(self):
        """Test that mismatched cols_per_row raises error."""
        with pytest.raises(ValueError, match="cols_per_row must match"):
            GrinSimulator(rows=3, cols_per_row=[5, 7])  # Only 2 values for 3 rows

    def test_divide_into_sections_small(self):
        """Test section division for small layouts."""
        sim = GrinSimulator(rows=1, cols=3)
        sections = sim._divide_into_sections()

        assert len(sections) == 1
        assert len(sections[0]) > 0

    def test_divide_into_sections_large(self):
        """Test section division for larger layouts."""
        sim = GrinSimulator(rows=3, cols=10)
        sections = sim._divide_into_sections()

        assert len(sections) == 3
        for row_sections in sections:
            # Should have H → L → U → L → H pattern
            assert len(row_sections) == 5
            assert row_sections[0].type == SectionType.HORIZONTAL
            assert row_sections[1].type == SectionType.LOWER_ARC
            assert row_sections[2].type == SectionType.UPPER_ARC
            assert row_sections[3].type == SectionType.LOWER_ARC
            assert row_sections[4].type == SectionType.HORIZONTAL

    def test_layout_execution(self):
        """Test that layout() executes without errors."""
        sim = GrinSimulator(rows=3, cols=10)
        sim.layout()

        # Check that footprints have been positioned
        for row in sim.footprints:
            for fp in row:
                # Position should be set (not at origin for all keys)
                assert fp.x is not None
                assert fp.y is not None

    def test_layout_spacing_evaluation(self):
        """Test that spacing evaluation works after layout."""
        sim = GrinSimulator(rows=2, cols=5, base_radius=150.0)
        sim.layout()

        spacing = sim.evaluate_spacing()
        # Just verify that spacing evaluation completes and returns valid results
        assert 'interferences' in spacing
        assert 'pairs' in spacing
        assert len(spacing['pairs']) > 0

    def test_get_all_footprints(self):
        """Test getting all footprints as flat list."""
        sim = GrinSimulator(rows=3, cols=5)
        all_fps = sim.get_all_footprints()

        assert len(all_fps) == 15  # 3 rows × 5 cols

    def test_evaluate_spacing_wrapper(self):
        """Test the convenience spacing evaluation wrapper."""
        sim = GrinSimulator(rows=2, cols=5)
        sim.layout()

        spacing = sim.evaluate_spacing(gap_threshold=1.0)

        assert 'pairs' in spacing
        assert 'interferences' in spacing
        assert 'min_gap' in spacing
        # Should have multiple pairs checked
        assert len(spacing['pairs']) > 0

    def test_print_layout_summary(self, capsys):
        """Test that layout summary prints without errors."""
        sim = GrinSimulator(rows=2, cols=5)
        sim.layout()
        sim.print_layout_summary()

        captured = capsys.readouterr()
        assert 'Grin Array Layout Summary' in captured.out
        assert 'Rows: 2' in captured.out
