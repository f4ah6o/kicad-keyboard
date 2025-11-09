"""
Core API functions for Grin array keyboard layout.
Implements the minimal API as specified in plan.md.
"""
import numpy as np
from typing import Tuple, Optional, Union
from footprint import Footprint


# ============================================================================
# Utility Functions
# ============================================================================

def circle_point(C: Tuple[float, float], R: float, theta: float) -> Tuple[float, float]:
    """
    Calculate a point on a circle.

    Args:
        C: Center point (Cx, Cy)
        R: Radius
        theta: Angle in radians

    Returns:
        Point (x, y) on the circle
    """
    x = C[0] + R * np.cos(theta)
    y = C[1] + R * np.sin(theta)
    return (x, y)


def angle_step(pitch: float, R: float) -> float:
    """
    Calculate the angular step between keys on an arc.

    Args:
        pitch: Distance between key centers
        R: Radius of the arc

    Returns:
        Angular step in radians
    """
    # Ensure pitch/(2*R) <= 1 for numerical stability
    ratio = pitch / (2 * R)
    if ratio > 1.0:
        raise ValueError(f"pitch/(2*R) = {ratio} > 1.0. Increase R or decrease pitch.")

    return 2 * np.arcsin(ratio)


# ============================================================================
# Core API Functions
# ============================================================================

def place_on_arc(fp: Footprint, C: Tuple[float, float], R: float, theta: float):
    """
    Place a footprint on an arc at the specified angle.

    Args:
        fp: Footprint to place
        C: Center point of the arc (Cx, Cy)
        R: Radius of the arc
        theta: Angle in radians (measured from positive x-axis)

    Effect:
        Moves fp's origin (center) to C + R*(cos(theta), sin(theta))
    """
    x, y = circle_point(C, R, theta)
    fp.move_to(x, y)


def orient_to_tangent(fp: Footprint, theta: float, orientation: str, y_up: bool = True):
    """
    Orient a footprint tangent to an arc.

    Args:
        fp: Footprint to orient
        theta: Angle in radians (position on the arc)
        orientation: "UPPER" or "LOWER" (which side of the arc)
        y_up: True if y-axis points up, False if it points down

    Effect:
        Rotates fp to be tangent to the arc.
        Formula: rotation = theta + (+90° if UPPER else -90°)
        If y_up=False, flip the sign.
    """
    if orientation not in ["UPPER", "LOWER"]:
        raise ValueError(f"orientation must be 'UPPER' or 'LOWER', got '{orientation}'")

    # Calculate tangent angle
    if orientation == "UPPER":
        rotation = theta + np.pi / 2  # +90 degrees
    else:  # LOWER
        rotation = theta - np.pi / 2  # -90 degrees

    # Flip sign if y-axis points down
    if not y_up:
        rotation = -rotation

    fp.rotate_to(rotation)


def snap_corner(
    fp: Footprint,
    which: str,
    target: Union[Tuple[float, float], Tuple[Footprint, str]]
):
    """
    Snap a corner of the footprint to a target position or another footprint's corner.

    Args:
        fp: Footprint to move
        which: Which corner to snap ('center_side', 'NE', 'NW', 'SE', 'SW')
        target: Either a (x, y) position, or a tuple (other_fp, corner_name)

    Effect:
        Translates fp so that the specified corner matches the target.
        Rotation is preserved.
    """
    # Determine target position
    if isinstance(target, tuple) and len(target) == 2:
        if isinstance(target[0], Footprint):
            # Target is (other_fp, corner_name)
            other_fp, other_corner = target
            target_pos = other_fp.get_corner(other_corner)
        else:
            # Target is (x, y)
            target_pos = target
    else:
        raise ValueError("target must be (x, y) or (Footprint, corner_name)")

    # Get current corner position
    if which == 'center_side':
        # This is a special case - we need to know the center to determine which corner
        # For now, we'll need to pass the center separately or store it in the footprint
        # Let's add a method to determine this
        raise NotImplementedError("'center_side' requires additional context. Use specific corner names or extend the API.")
    else:
        current_pos = fp.get_corner(which)

    # Calculate offset
    dx = target_pos[0] - current_pos[0]
    dy = target_pos[1] - current_pos[1]

    # Move the footprint
    fp.move_to(fp.x + dx, fp.y + dy)


def snap_corner_to_center_side(
    fp: Footprint,
    target: Union[Tuple[float, float], Tuple[Footprint, Tuple[float, float]]],
    center: Tuple[float, float]
):
    """
    Snap the center-side corner of the footprint to a target.
    This is a helper for the common case of snapping to the corner closest to the arc center.

    Args:
        fp: Footprint to move
        target: Either a (x, y) position, or a tuple (other_fp, center)
        center: The arc center point, used to determine which corner is "center_side"

    Effect:
        Translates fp so that its center-side corner matches the target.
    """
    # Determine target position
    if isinstance(target, tuple) and len(target) == 2:
        if isinstance(target[0], Footprint):
            # Target is (other_fp, center)
            other_fp, center_for_other = target
            other_corner_name = other_fp.get_center_side_corner(center_for_other)
            target_pos = other_fp.get_corner(other_corner_name)
        else:
            # Target is (x, y)
            target_pos = target
    else:
        raise ValueError("target must be (x, y) or (Footprint, center)")

    # Determine which corner is center-side for this footprint
    corner_name = fp.get_center_side_corner(center)

    # Get current corner position
    current_pos = fp.get_corner(corner_name)

    # Calculate offset
    dx = target_pos[0] - current_pos[0]
    dy = target_pos[1] - current_pos[1]

    # Move the footprint
    fp.move_to(fp.x + dx, fp.y + dy)
