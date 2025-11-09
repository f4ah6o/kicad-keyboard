"""
Footprint data structure for keyboard key simulation.
"""
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class Footprint:
    """Represents a keyboard key footprint."""

    # Identity
    row: int
    col: int

    # Position and orientation
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0  # in radians

    # Dimensions (in mm)
    width: float = 19.05  # 1U key width
    height: float = 19.05  # 1U key height

    def __post_init__(self):
        """Initialize corner cache."""
        self._corner_cache = None

    @property
    def center(self) -> Tuple[float, float]:
        """Get the center position."""
        return (self.x, self.y)

    def get_corners(self) -> dict:
        """
        Get all four corners of the footprint in world coordinates.
        Returns: dict with keys 'NE', 'NW', 'SE', 'SW'
        """
        # Half dimensions
        hw = self.width / 2
        hh = self.height / 2

        # Local corners (before rotation)
        local_corners = {
            'NE': (hw, hh),
            'NW': (-hw, hh),
            'SE': (hw, -hh),
            'SW': (-hw, -hh),
        }

        # Rotation matrix
        cos_r = np.cos(self.rotation)
        sin_r = np.sin(self.rotation)

        # Transform to world coordinates
        world_corners = {}
        for name, (lx, ly) in local_corners.items():
            wx = self.x + lx * cos_r - ly * sin_r
            wy = self.y + lx * sin_r + ly * cos_r
            world_corners[name] = (wx, wy)

        return world_corners

    def get_corner(self, which: str) -> Tuple[float, float]:
        """Get a specific corner position."""
        corners = self.get_corners()
        return corners[which]

    def get_center_side_corner(self, center: Tuple[float, float]) -> str:
        """
        Find the corner closest to the given center point.
        This is used for arc placement where keys should touch at their center-side corners.

        For landscape keys (width > height), only consider corners on the short edge.
        """
        corners = self.get_corners()

        # For landscape keys, only consider corners on short edges
        if self.width > self.height:
            # Short edges are top and bottom, so consider NE, NW, SE, SW
            # But we want corners on the short dimension
            # Actually, for a horizontal key, the short edges are left and right
            # Let me reconsider: if width > height, the key is horizontal
            # The short edges are top and bottom (height dimension)
            # So we consider all corners but prefer those closer to center
            candidate_corners = ['NE', 'NW', 'SE', 'SW']
        elif self.height > self.width:
            # Vertical key - short edges are left and right
            candidate_corners = ['NE', 'NW', 'SE', 'SW']
        else:
            # Square key
            candidate_corners = ['NE', 'NW', 'SE', 'SW']

        # Find the corner with minimum distance to center
        min_dist = float('inf')
        closest = None

        for corner_name in candidate_corners:
            cx, cy = corners[corner_name]
            dist = np.sqrt((cx - center[0])**2 + (cy - center[1])**2)
            if dist < min_dist:
                min_dist = dist
                closest = corner_name

        return closest

    def move_to(self, x: float, y: float):
        """Move the footprint center to the specified position."""
        self.x = x
        self.y = y
        self._corner_cache = None

    def rotate_to(self, rotation: float):
        """Set the rotation to the specified angle (in radians)."""
        self.rotation = rotation
        self._corner_cache = None

    def __repr__(self):
        return f"Footprint(r{self.row}c{self.col}, pos=({self.x:.2f},{self.y:.2f}), rot={np.degrees(self.rotation):.1f}°)"
