"""Tests for api module."""
import pytest
import numpy as np
from footprint import Footprint
from api import (
    circle_point,
    angle_step,
    place_on_arc,
    orient_to_tangent,
    snap_corner,
    snap_corner_to_center_side,
    footprint_spacing,
    evaluate_spacing,
)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_circle_point_basic(self):
        """Test circle_point with basic parameters."""
        center = (100.0, 100.0)
        radius = 50.0
        theta = 0.0  # Point at 3 o'clock

        point = circle_point(center, radius, theta)
        assert np.allclose(point, (150.0, 100.0))

    def test_circle_point_90_degrees(self):
        """Test circle_point at 90 degrees."""
        center = (100.0, 100.0)
        radius = 50.0
        theta = np.pi / 2  # Point at 12 o'clock (or 6 o'clock with y_up=False)

        # With y_up=False (screen coords), positive angle goes down
        point = circle_point(center, radius, theta, y_up=False)
        assert np.allclose(point, (100.0, 50.0))  # Above center in screen coords

    def test_angle_step_valid(self):
        """Test angle_step with valid parameters."""
        pitch = 19.05
        radius = 100.0

        theta = angle_step(pitch, radius)
        assert theta > 0
        assert theta < np.pi

    def test_angle_step_invalid(self):
        """Test angle_step with invalid parameters (pitch too large)."""
        pitch = 300.0  # Too large for radius
        radius = 100.0

        with pytest.raises(ValueError, match="pitch/\\(2\\*R\\)"):
            angle_step(pitch, radius)


class TestCoreAPIFunctions:
    """Test core API functions."""

    def test_place_on_arc(self):
        """Test placing footprint on arc."""
        fp = Footprint(row=0, col=0)
        center = (100.0, 100.0)
        radius = 50.0
        theta = 0.0

        place_on_arc(fp, center, radius, theta)
        assert np.allclose((fp.x, fp.y), (150.0, 100.0))

    def test_orient_to_tangent_upper(self):
        """Test orienting footprint to upper arc tangent."""
        fp = Footprint(row=0, col=0)
        theta = 0.0

        orient_to_tangent(fp, theta, "UPPER", y_up=False)
        # For theta=0, upper tangent should be at -90 degrees (screen coords)
        assert np.isclose(fp.rotation, -np.pi/2)

    def test_orient_to_tangent_lower(self):
        """Test orienting footprint to lower arc tangent."""
        fp = Footprint(row=0, col=0)
        theta = 0.0

        orient_to_tangent(fp, theta, "LOWER", y_up=False)
        # For theta=0, lower tangent should be at +90 degrees (screen coords)
        assert np.isclose(fp.rotation, np.pi/2)

    def test_orient_to_tangent_invalid(self):
        """Test orient_to_tangent with invalid orientation."""
        fp = Footprint(row=0, col=0)

        with pytest.raises(ValueError, match="orientation must be"):
            orient_to_tangent(fp, 0.0, "INVALID")

    def test_snap_corner_to_position(self):
        """Test snapping corner to a position."""
        fp = Footprint(row=0, col=0, x=0.0, y=0.0, width=20.0, height=20.0)
        target = (100.0, 100.0)

        snap_corner(fp, 'NE', target)

        # NE corner should now be at (100, 100)
        ne_corner = fp.get_corner('NE')
        assert np.allclose(ne_corner, target)

    def test_snap_corner_to_footprint(self):
        """Test snapping corner to another footprint's corner."""
        fp1 = Footprint(row=0, col=0, x=100.0, y=100.0, width=20.0, height=20.0)
        fp2 = Footprint(row=0, col=1, x=0.0, y=0.0, width=20.0, height=20.0)

        # Snap fp2's NW corner to fp1's NE corner
        snap_corner(fp2, 'NW', (fp1, 'NE'))

        # Corners should match
        fp1_ne = fp1.get_corner('NE')
        fp2_nw = fp2.get_corner('NW')
        assert np.allclose(fp1_ne, fp2_nw)


class TestSpacingFunctions:
    """Test spacing and interference detection."""

    def test_footprint_spacing_clearance(self):
        """Test spacing with clear separation."""
        fp1 = Footprint(row=0, col=0, x=0.0, y=0.0, width=10.0, height=10.0)
        fp2 = Footprint(row=0, col=1, x=20.0, y=0.0, width=10.0, height=10.0)

        result = footprint_spacing(fp1, fp2)

        assert result['status'] == 'CLEARANCE'
        assert result['gap'] > 0
        assert result['penetration'] == 0.0

    def test_footprint_spacing_contact(self):
        """Test spacing with contact (touching)."""
        fp1 = Footprint(row=0, col=0, x=0.0, y=0.0, width=10.0, height=10.0)
        fp2 = Footprint(row=0, col=1, x=10.0, y=0.0, width=10.0, height=10.0)

        result = footprint_spacing(fp1, fp2)

        # Should be contact or very close
        assert result['status'] in ['CONTACT', 'CLEARANCE']
        if result['status'] == 'CLEARANCE':
            assert result['gap'] < 1e-3

    def test_footprint_spacing_interference(self):
        """Test spacing with overlap."""
        fp1 = Footprint(row=0, col=0, x=0.0, y=0.0, width=10.0, height=10.0)
        fp2 = Footprint(row=0, col=1, x=5.0, y=0.0, width=10.0, height=10.0)

        result = footprint_spacing(fp1, fp2)

        assert result['status'] == 'INTERFERENCE'
        assert result['penetration'] > 0

    def test_evaluate_spacing_multiple(self):
        """Test evaluating spacing for multiple footprints."""
        footprints = [
            Footprint(row=0, col=0, x=0.0, y=0.0, width=10.0, height=10.0),
            Footprint(row=0, col=1, x=20.0, y=0.0, width=10.0, height=10.0),
            Footprint(row=0, col=2, x=40.0, y=0.0, width=10.0, height=10.0),
        ]

        summary = evaluate_spacing(footprints, gap_threshold=5.0)

        assert 'pairs' in summary
        assert 'interferences' in summary
        assert 'small_gaps' in summary
        assert 'min_gap' in summary
        assert len(summary['pairs']) == 3  # 3 choose 2 = 3 pairs
