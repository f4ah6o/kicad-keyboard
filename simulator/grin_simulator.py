"""
Grin Array Keyboard Layout Simulator.
Implements the workflow described in plan.md.
"""
import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

from footprint import Footprint
from api import (
    place_on_arc,
    orient_to_tangent,
    snap_corner_to_center_side,
    angle_step,
    circle_point,
    evaluate_spacing,
)


class SectionType(Enum):
    """Type of layout section."""
    HORIZONTAL = "H"
    UPPER_ARC = "UPPER"
    LOWER_ARC = "LOWER"


@dataclass
class Section:
    """Represents a section of keys in a row."""
    type: SectionType
    cols: List[int]  # Column indices in this section
    theta0: float = 0.0  # Starting angle for arc sections


class GrinSimulator:
    """
    Simulator for Grin array keyboard layout.

    The Grin array uses a pattern of: horizontal → lower arc → upper arc → lower arc → horizontal
    """

    def __init__(
        self,
        rows: int = 3,
        cols: int = 10,
        center: Tuple[float, float] = (100.0, 100.0),
        base_radius: float = 150.0,
        radius_step: float = 20.0,
        base_pitch: float = 19.05,
        y_up: bool = False,
        cols_per_row: List[int] | None = None,
    ):
        """
        Initialize the Grin simulator.

        Args:
            rows: Number of rows
            cols: Number of columns
            center: Common center point (Cx, Cy) for all arcs
            base_radius: Radius for the top row
            radius_step: Radius decrease per row (bottom rows have smaller radius)
            base_pitch: Key pitch (center-to-center distance)
            y_up: Whether the positive Y axis points upward (default False for screen coords)
            cols_per_row: Optional explicit column counts per row (default: uniform)
        """
        self.rows = rows
        if cols_per_row is not None:
            if len(cols_per_row) != rows:
                raise ValueError("cols_per_row must match the number of rows")
            self.cols_per_row = cols_per_row
            self.cols = max(cols_per_row) if cols_per_row else cols
        else:
            self.cols = cols
            self.cols_per_row = [cols for _ in range(rows)]
        self.center = center
        self.base_radius = base_radius
        self.radius_step = radius_step
        self.base_pitch = base_pitch
        self.y_up = y_up

        # Calculate radius and pitch for each row
        # Top row (row 0) has largest radius, bottom row has smallest
        self.R = [base_radius - r * radius_step for r in range(rows)]
        self.P = [base_pitch for _ in range(rows)]  # Same pitch for all rows

        # Create footprints
        self.footprints: List[List[Footprint]] = []
        for r in range(rows):
            row_fps = []
            for c in range(self.cols_per_row[r]):
                fp = Footprint(row=r, col=c)
                row_fps.append(fp)
            self.footprints.append(row_fps)

        # Section definitions (will be computed)
        self.sections: List[List[Section]] = []

    def _divide_into_sections(self) -> List[List[Section]]:
        """
        Divide each row into sections: H → L → U → L → H

        Returns:
            List of sections for each row
        """
        sections = []

        for r in range(self.rows):
            row_sections = []
            total_cols = len(self.footprints[r])

            if total_cols == 0:
                sections.append(row_sections)
                continue

            # Simple division pattern for demonstration
            # Adjust these numbers based on your specific layout needs
            if total_cols >= 9:
                # Left horizontal: 2 keys
                # Lower arc left: 2 keys
                # Upper arc: 3 keys (center)
                # Lower arc right: 2 keys
                # Right horizontal: remaining keys

                left_h = 2
                left_lower = 2
                upper = 3
                right_lower = 2
                right_h = total_cols - left_h - left_lower - upper - right_lower

                sections_def = [
                    (SectionType.HORIZONTAL, left_h),
                    (SectionType.LOWER_ARC, left_lower),
                    (SectionType.UPPER_ARC, upper),
                    (SectionType.LOWER_ARC, right_lower),
                    (SectionType.HORIZONTAL, right_h),
                ]
            elif total_cols >= 5:
                middle = max(total_cols - 4, 1)
                sections_def = [
                    (SectionType.HORIZONTAL, 1),
                    (SectionType.LOWER_ARC, 1),
                    (SectionType.UPPER_ARC, middle),
                    (SectionType.LOWER_ARC, 1),
                    (SectionType.HORIZONTAL, 1),
                ]
            else:
                sections_def = [(SectionType.HORIZONTAL, total_cols)]

            # Create sections with column indices
            col_idx = 0
            for sec_type, count in sections_def:
                if count > 0:
                    cols_in_section = list(range(col_idx, col_idx + count))
                    row_sections.append(Section(type=sec_type, cols=cols_in_section))
                    col_idx += count

            sections.append(row_sections)

        return sections

    def layout(self):
        """
        Perform the complete layout process.
        """
        # Step 1: Divide into sections
        self.sections = self._divide_into_sections()

        # Step 2: Calculate angle steps for each row
        d_theta = []
        for r in range(self.rows):
            try:
                dt = angle_step(self.P[r], self.R[r])
                d_theta.append(dt)
            except ValueError as e:
                print(f"Warning: Row {r}: {e}")
                d_theta.append(0.1)  # Fallback value

        # Step 3: Layout each row
        for r in range(self.rows):
            self._layout_row(r, d_theta[r])

        # Step 4: Validate constraints
        self._validate_constraints()

    def _layout_row(self, r: int, d_theta: float):
        """
        Layout a single row.

        Args:
            r: Row index
            d_theta: Angular step for this row
        """
        sections = self.sections[r]
        current_angle = -np.pi / 4  # Start angle (can be adjusted)

        for sec in sections:
            if sec.type == SectionType.HORIZONTAL:
                self._place_horizontal_section(r, sec, current_angle)
            else:
                sec.theta0 = current_angle
                self._place_arc_section(r, sec, d_theta)
                # Update current angle for next section
                current_angle = sec.theta0 + len(sec.cols) * d_theta

    def _place_horizontal_section(self, r: int, sec: Section, base_angle: float):
        """
        Place keys in a horizontal section.

        Args:
            r: Row index
            sec: Section to place
            base_angle: Reference angle for positioning
        """
        # For horizontal sections, place keys in a straight line
        # Start from the arc position and continue horizontally
        start_pos = circle_point(self.center, self.R[r], base_angle, y_up=self.y_up)

        for i, c in enumerate(sec.cols):
            fp = self.footprints[r][c]
            # Place horizontally with equal spacing
            x = start_pos[0] + i * self.P[r]
            y = start_pos[1]
            fp.move_to(x, y)
            fp.rotate_to(0.0)  # No rotation for horizontal keys

    def _place_arc_section(self, r: int, sec: Section, d_theta: float):
        """
        Place keys in an arc section using the minimal API sequence.

        Args:
            r: Row index
            sec: Section to place
            d_theta: Angular step
        """
        theta = sec.theta0
        prev_fp = None

        for c in sec.cols:
            fp = self.footprints[r][c]

            # Step 1: Place on arc
            place_on_arc(fp, self.center, self.R[r], theta, y_up=self.y_up)

            # Step 2: Orient to tangent
            orient_to_tangent(fp, theta, sec.type.value, y_up=self.y_up)

            # Step 3: Snap corner to previous key (corner contact)
            if prev_fp is not None:
                try:
                    snap_corner_to_center_side(
                        fp,
                        target=(prev_fp, self.center),
                        center=self.center
                    )
                except Exception as e:
                    print(f"Warning: Failed to snap corner for r{r}c{c}: {e}")

            prev_fp = fp
            theta += d_theta

    def _validate_constraints(self):
        """
        Validate layout constraints.
        - Lower arc sections should have at most 2 keys on each side (except bottom row)
        """
        for r in range(self.rows - 1):  # Exclude bottom row
            lower_sections = [s for s in self.sections[r] if s.type == SectionType.LOWER_ARC]

            for sec in lower_sections:
                if len(sec.cols) > 2:
                    print(f"Warning: Row {r} has a lower arc section with {len(sec.cols)} keys (max 2)")

    def get_all_footprints(self) -> List[Footprint]:
        """Get all footprints as a flat list."""
        result = []
        for row in self.footprints:
            result.extend(row)
        return result

    def evaluate_spacing(self, gap_threshold: float = 0.5):
        """Convenience wrapper for spacing analysis across the layout."""
        return evaluate_spacing(self.get_all_footprints(), gap_threshold=gap_threshold)

    def print_layout_summary(self):
        """Print a summary of the layout."""
        print(f"\n{'='*60}")
        print(f"Grin Array Layout Summary")
        print(f"{'='*60}")
        print(f"Rows: {self.rows}, Max Cols: {self.cols}")
        print(f"Cols per row: {', '.join(str(len(row)) for row in self.footprints)}")
        print(f"Center: {self.center}")
        print(f"Base Radius: {self.base_radius}, Step: {self.radius_step}")
        print(f"Base Pitch: {self.base_pitch}")
        print()

        for r in range(self.rows):
            print(f"Row {r}: R={self.R[r]:.2f}mm")
            for sec in self.sections[r]:
                print(f"  {sec.type.value:12s} cols {sec.cols[0]:2d}-{sec.cols[-1]:2d} ({len(sec.cols)} keys)")

        print(f"{'='*60}\n")
