"""
Grin Array Keyboard Layout Simulator.

A Python-based simulator for generating Grin array keyboard layouts
using minimal API functions as specified in plan.md.
"""

from .footprint import Footprint
from .api import (
    place_on_arc,
    orient_to_tangent,
    snap_corner,
    snap_corner_to_center_side,
    angle_step,
    circle_point,
)
from .grin_simulator import GrinSimulator, Section, SectionType
from .visualizer import GrinVisualizer, plot_grin_layout

__version__ = "0.1.0"

__all__ = [
    # Data structures
    "Footprint",
    "Section",
    "SectionType",
    # Core API
    "place_on_arc",
    "orient_to_tangent",
    "snap_corner",
    "snap_corner_to_center_side",
    "angle_step",
    "circle_point",
    # Simulator
    "GrinSimulator",
    # Visualization
    "GrinVisualizer",
    "plot_grin_layout",
]
