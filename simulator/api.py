"""
Core API functions for Grin array keyboard layout.
Implements the minimal API as specified in plan.md.
"""
import math
from itertools import combinations
from typing import Iterable, List, Tuple, Union

import numpy as np

from footprint import Footprint


# ============================================================================
# Utility Functions
# ============================================================================

def circle_point(
    C: Tuple[float, float],
    R: float,
    theta: float,
    *,
    y_up: bool = False,
) -> Tuple[float, float]:
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
    y = C[1] + (R * np.sin(theta) if y_up else -R * np.sin(theta))
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

def place_on_arc(
    fp: Footprint,
    C: Tuple[float, float],
    R: float,
    theta: float,
    *,
    R_inner: float | None = None,
    R_outer: float | None = None,
    y_up: bool = False,
):
    """
    Place a footprint on an arc at the specified angle.

    For arc-based keyboard layouts, three reference circles are used:
    - R_center (R): The center circle through key centers (used for angle calculation)
    - R_inner: The inner circle through the inner edges of keys (closest to arc center)
    - R_outer: The outer circle through the outer edges of keys (farthest from arc center)

    Args:
        fp: Footprint to place
        C: Center point of the arc (Cx, Cy)
        R: Radius of the center reference circle (key centers)
        theta: Angle in radians (measured from positive x-axis)
        R_inner: Radius of the inner reference circle (optional)
        R_outer: Radius of the outer reference circle (optional)
        y_up: True if y-axis points up, False if it points down

    Effect:
        Moves fp's origin (center) to C + R*(cos(theta), sin(theta))
        The three reference circles are used for precise arc layout calculations.

    Note:
        If R_inner and R_outer are not provided, they can be calculated from R
        after the footprint is oriented, using the key's radial dimension:
        - R_inner = R - (key_radial_dimension / 2)
        - R_outer = R + (key_radial_dimension / 2)
    """
    x, y = circle_point(C, R, theta, y_up=y_up)
    fp.move_to(x, y)

    # Store reference circle parameters for potential future use
    # This allows downstream code to access the three reference circles
    if not hasattr(fp, '_arc_params'):
        fp._arc_params = {}
    fp._arc_params['R_center'] = R
    fp._arc_params['R_inner'] = R_inner
    fp._arc_params['R_outer'] = R_outer
    fp._arc_params['theta'] = theta
    fp._arc_params['C'] = C


def orient_to_tangent(
    fp: Footprint,
    theta: float,
    orientation: str,
    y_up: bool = False,
):
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


# ============================================================================
# Spacing / Interference Evaluation
# ============================================================================

def _ordered_corners(fp: Footprint) -> List[Tuple[float, float]]:
    corners = fp.get_corners()
    order = ['NW', 'NE', 'SE', 'SW']
    return [corners[name] for name in order]


def _edge_vectors(polygon: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    edges = []
    for idx in range(len(polygon)):
        x1, y1 = polygon[idx]
        x2, y2 = polygon[(idx + 1) % len(polygon)]
        edges.append((x2 - x1, y2 - y1))
    return edges


def _normalize(vec: Tuple[float, float]) -> Tuple[float, float]:
    vx, vy = vec
    length = math.hypot(vx, vy)
    if length == 0:
        return (0.0, 0.0)
    return (vx / length, vy / length)


def _project_polygon(axis: Tuple[float, float], polygon: List[Tuple[float, float]]):
    dots = [axis[0] * px + axis[1] * py for px, py in polygon]
    return min(dots), max(dots)


def _sat_penetration(poly_a: List[Tuple[float, float]], poly_b: List[Tuple[float, float]]):
    min_overlap = float('inf')
    axes = _edge_vectors(poly_a) + _edge_vectors(poly_b)

    for edge in axes:
        axis = _normalize((-edge[1], edge[0]))
        if axis == (0.0, 0.0):
            continue

        min_a, max_a = _project_polygon(axis, poly_a)
        min_b, max_b = _project_polygon(axis, poly_b)
        overlap = min(max_a, max_b) - max(min_a, min_b)

        if overlap <= 0:
            return False, 0.0

        if overlap < min_overlap:
            min_overlap = overlap

    return True, min_overlap if min_overlap != float('inf') else 0.0


def _point_segment_distance(point, seg_start, seg_end) -> float:
    px, py = point
    x1, y1 = seg_start
    x2, y2 = seg_end
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)

    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    return math.hypot(px - closest_x, py - closest_y)


def _polygon_min_distance(poly_a: List[Tuple[float, float]], poly_b: List[Tuple[float, float]]):
    min_dist = float('inf')

    def iter_edges(poly):
        for idx in range(len(poly)):
            yield poly[idx], poly[(idx + 1) % len(poly)]

    for point in poly_a:
        for seg_start, seg_end in iter_edges(poly_b):
            min_dist = min(min_dist, _point_segment_distance(point, seg_start, seg_end))

    for point in poly_b:
        for seg_start, seg_end in iter_edges(poly_a):
            min_dist = min(min_dist, _point_segment_distance(point, seg_start, seg_end))

    return 0.0 if min_dist == float('inf') else min_dist


def footprint_spacing(fp_a: Footprint, fp_b: Footprint):
    """Evaluate spacing between two footprints.

    Returns:
        dict with gap (positive distance), penetration (overlap depth),
        and status: CLEARANCE, CONTACT, or INTERFERENCE.
    """

    poly_a = _ordered_corners(fp_a)
    poly_b = _ordered_corners(fp_b)

    overlapping, penetration = _sat_penetration(poly_a, poly_b)
    if overlapping:
        gap = 0.0
        status = "INTERFERENCE" if penetration > 1e-6 else "CONTACT"
    else:
        penetration = 0.0
        gap = _polygon_min_distance(poly_a, poly_b)
        status = "CONTACT" if gap <= 1e-6 else "CLEARANCE"

    pair = {
        "a": {"row": fp_a.row, "col": fp_a.col},
        "b": {"row": fp_b.row, "col": fp_b.col},
        "gap": float(gap),
        "penetration": float(penetration),
        "status": status,
    }

    return pair


def evaluate_spacing(
    footprints: Iterable[Footprint],
    gap_threshold: float = 0.5,
):
    """Evaluate pairwise spacing for an iterable of footprints."""

    fp_list = list(footprints)
    summary = {
        "pairs": [],
        "interferences": [],
        "small_gaps": [],
        "min_gap": None,
        "min_gap_pair": None,
    }

    for fp_a, fp_b in combinations(fp_list, 2):
        result = footprint_spacing(fp_a, fp_b)
        summary["pairs"].append(result)

        if result["status"] == "INTERFERENCE":
            summary["interferences"].append(result)
        else:
            gap = result["gap"]
            if summary["min_gap"] is None or gap < summary["min_gap"]:
                summary["min_gap"] = gap
                summary["min_gap_pair"] = result

            if gap <= gap_threshold:
                summary["small_gaps"].append(result)

    return summary
