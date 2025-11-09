"""Tests for footprint module."""
import pytest
import numpy as np
from footprint import Footprint


class TestFootprint:
    """Test cases for Footprint class."""

    def test_footprint_creation(self):
        """Test basic footprint creation."""
        fp = Footprint(row=0, col=0)
        assert fp.row == 0
        assert fp.col == 0
        assert fp.x == 0.0
        assert fp.y == 0.0
        assert fp.rotation == 0.0

    def test_footprint_with_position(self):
        """Test footprint creation with initial position."""
        fp = Footprint(row=1, col=2, x=10.0, y=20.0, rotation=np.pi/4)
        assert fp.row == 1
        assert fp.col == 2
        assert fp.x == 10.0
        assert fp.y == 20.0
        assert fp.rotation == np.pi/4

    def test_center_property(self):
        """Test center property."""
        fp = Footprint(row=0, col=0, x=15.0, y=25.0)
        assert fp.center == (15.0, 25.0)

    def test_move_to(self):
        """Test moving footprint."""
        fp = Footprint(row=0, col=0)
        fp.move_to(10.0, 20.0)
        assert fp.x == 10.0
        assert fp.y == 20.0

    def test_rotate_to(self):
        """Test rotating footprint."""
        fp = Footprint(row=0, col=0)
        fp.rotate_to(np.pi/2)
        assert np.isclose(fp.rotation, np.pi/2)

    def test_get_corners_no_rotation(self):
        """Test getting corners without rotation."""
        fp = Footprint(row=0, col=0, x=0.0, y=0.0, width=20.0, height=20.0)
        corners = fp.get_corners()

        assert 'NE' in corners
        assert 'NW' in corners
        assert 'SE' in corners
        assert 'SW' in corners

        # For a centered 20x20 footprint at origin
        assert np.allclose(corners['NE'], (10.0, 10.0))
        assert np.allclose(corners['NW'], (-10.0, 10.0))
        assert np.allclose(corners['SE'], (10.0, -10.0))
        assert np.allclose(corners['SW'], (-10.0, -10.0))

    def test_get_corners_with_rotation(self):
        """Test getting corners with 90 degree rotation."""
        fp = Footprint(row=0, col=0, x=0.0, y=0.0, width=20.0, height=20.0)
        fp.rotate_to(np.pi/2)  # 90 degrees
        corners = fp.get_corners()

        # After 90 degree rotation, corners should swap
        assert np.allclose(corners['NE'], (-10.0, 10.0), atol=1e-10)
        assert np.allclose(corners['NW'], (-10.0, -10.0), atol=1e-10)

    def test_get_corner(self):
        """Test getting a specific corner."""
        fp = Footprint(row=0, col=0, x=0.0, y=0.0, width=20.0, height=20.0)
        ne_corner = fp.get_corner('NE')
        assert np.allclose(ne_corner, (10.0, 10.0))

    def test_get_center_side_corner(self):
        """Test finding the center-side corner."""
        fp = Footprint(row=0, col=0, x=100.0, y=0.0, width=20.0, height=20.0)
        center = (0.0, 0.0)

        # The corner closest to (0, 0) from position (100, 0)
        # should be on the left side (NW or SW)
        corner_name = fp.get_center_side_corner(center)
        assert corner_name in ['NW', 'SW']

    def test_repr(self):
        """Test string representation."""
        fp = Footprint(row=2, col=3, x=10.5, y=20.5)
        repr_str = repr(fp)
        assert 'r2c3' in repr_str
        assert '10.5' in repr_str or '10.50' in repr_str
        assert '20.5' in repr_str or '20.50' in repr_str
