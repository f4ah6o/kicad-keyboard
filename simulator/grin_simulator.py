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
    center: Tuple[float, float] | None = None  # Center point for this section
    radius_base: float | None = None  # Base radius for this section


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
        # Three-center configuration (optional)
        C_lower1: Tuple[float, float] | None = None,
        C_upper: Tuple[float, float] | None = None,
        C_lower2: Tuple[float, float] | None = None,
        R_lower1_base: float | None = None,
        R_upper_base: float | None = None,
        R_lower2_base: float | None = None,
    ):
        """
        Initialize the Grin simulator.

        Args:
            rows: Number of rows
            cols: Number of columns
            center: Common center point (Cx, Cy) for all arcs (legacy mode)
            base_radius: Radius for the top row (legacy mode)
            radius_step: Radius decrease per row (bottom rows have smaller radius)
            base_pitch: Key pitch (center-to-center distance)
            y_up: Whether the positive Y axis points upward (default False for screen coords)
            cols_per_row: Optional explicit column counts per row (default: uniform)
            C_lower1: Center for left lower arc sections (three-center mode)
            C_upper: Center for upper arc sections (three-center mode)
            C_lower2: Center for right lower arc sections (three-center mode)
            R_lower1_base: Base radius for left lower arcs (three-center mode)
            R_upper_base: Base radius for upper arcs (three-center mode)
            R_lower2_base: Base radius for right lower arcs (three-center mode, typically = R_lower1_base)
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

        # Determine if using three-center mode
        self.three_center_mode = C_lower1 is not None and C_upper is not None and C_lower2 is not None

        if self.three_center_mode:
            # Three-center mode: each arc section has its own center
            self.C_lower1 = C_lower1
            self.C_upper = C_upper
            self.C_lower2 = C_lower2
            self.R_lower1_base = R_lower1_base if R_lower1_base is not None else base_radius
            self.R_upper_base = R_upper_base if R_upper_base is not None else base_radius
            self.R_lower2_base = R_lower2_base if R_lower2_base is not None else self.R_lower1_base
            # Keep legacy fields for compatibility
            self.center = center
            self.base_radius = base_radius
        else:
            # Legacy mode: single center for all arcs
            self.center = center
            self.base_radius = base_radius
            self.C_lower1 = center
            self.C_upper = center
            self.C_lower2 = center
            self.R_lower1_base = base_radius
            self.R_upper_base = base_radius
            self.R_lower2_base = base_radius

        self.radius_step = radius_step
        self.base_pitch = base_pitch
        self.y_up = y_up

        # Calculate radius and pitch for each row
        # Top row (row 0) has largest radius, bottom row has smallest
        # For arc layouts, we need three reference circles:
        # - R_center: circle through key centers (for angle calculation)
        # - R_inner: circle through inner edges (closest to center)
        # - R_outer: circle through outer edges (farthest from center)

        # In three-center mode, we have different base radii for different sections
        # Store radii per row per section type
        self.R_center_lower1 = [self.R_lower1_base - r * radius_step for r in range(rows)]
        self.R_center_upper = [self.R_upper_base - r * radius_step for r in range(rows)]
        self.R_center_lower2 = [self.R_lower2_base - r * radius_step for r in range(rows)]

        # Legacy: use upper arc radii as default
        self.R_center = self.R_center_upper
        self.R = self.R_center

        self.P = [base_pitch for _ in range(rows)]  # Same pitch for all rows

        # Create footprints
        self.footprints: List[List[Footprint]] = []
        for r in range(rows):
            row_fps = []
            for c in range(self.cols_per_row[r]):
                fp = Footprint(row=r, col=c)
                row_fps.append(fp)
            self.footprints.append(row_fps)

        # Calculate inner and outer radii based on key height (radial dimension)
        # Assuming keys are oriented tangent to the arc, height is the radial dimension
        # In three-center mode, these are calculated per section type
        self.R_inner_lower1 = []
        self.R_outer_lower1 = []
        self.R_inner_upper = []
        self.R_outer_upper = []
        self.R_inner_lower2 = []
        self.R_outer_lower2 = []

        for r in range(rows):
            # Get key height from first footprint in the row
            if len(self.footprints[r]) > 0:
                key_height = self.footprints[r][0].height
            else:
                key_height = 19.05  # Default 1U key height

            self.R_inner_lower1.append(self.R_center_lower1[r] - key_height / 2)
            self.R_outer_lower1.append(self.R_center_lower1[r] + key_height / 2)
            self.R_inner_upper.append(self.R_center_upper[r] - key_height / 2)
            self.R_outer_upper.append(self.R_center_upper[r] + key_height / 2)
            self.R_inner_lower2.append(self.R_center_lower2[r] - key_height / 2)
            self.R_outer_lower2.append(self.R_center_lower2[r] + key_height / 2)

        # Legacy: use upper arc radii as default
        self.R_inner = self.R_inner_upper
        self.R_outer = self.R_outer_upper

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
            lower_arc_count = 0  # Track which lower arc section this is (left=0, right=1)
            for sec_type, count in sections_def:
                if count > 0:
                    cols_in_section = list(range(col_idx, col_idx + count))

                    # Assign center and radius based on section type
                    if sec_type == SectionType.LOWER_ARC:
                        if lower_arc_count == 0:
                            # Left lower arc
                            center = self.C_lower1
                            radius_base = self.R_lower1_base
                        else:
                            # Right lower arc
                            center = self.C_lower2
                            radius_base = self.R_lower2_base
                        lower_arc_count += 1
                    elif sec_type == SectionType.UPPER_ARC:
                        center = self.C_upper
                        radius_base = self.R_upper_base
                    else:
                        # Horizontal sections don't use arc parameters
                        center = None
                        radius_base = None

                    row_sections.append(Section(
                        type=sec_type,
                        cols=cols_in_section,
                        center=center,
                        radius_base=radius_base
                    ))
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
        # Get section-specific center and radii
        section_center = sec.center if sec.center is not None else self.center

        # Determine which radius arrays to use based on section type
        if sec.type == SectionType.LOWER_ARC:
            # Check if this is left or right lower arc based on the center
            if section_center == self.C_lower1:
                R_center = self.R_center_lower1[r]
                R_inner = self.R_inner_lower1[r]
                R_outer = self.R_outer_lower1[r]
            else:  # C_lower2
                R_center = self.R_center_lower2[r]
                R_inner = self.R_inner_lower2[r]
                R_outer = self.R_outer_lower2[r]
        else:  # UPPER_ARC
            R_center = self.R_center_upper[r]
            R_inner = self.R_inner_upper[r]
            R_outer = self.R_outer_upper[r]

        theta = sec.theta0
        prev_fp = None

        for c in sec.cols:
            fp = self.footprints[r][c]

            # Step 1: Place on arc with three reference circles
            place_on_arc(
                fp,
                section_center,
                R_center,
                theta,
                R_inner=R_inner,
                R_outer=R_outer,
                y_up=self.y_up
            )

            # Step 2: Orient to tangent
            orient_to_tangent(fp, theta, sec.type.value, y_up=self.y_up)

            # Step 3: Snap corner to previous key (corner contact)
            if prev_fp is not None:
                try:
                    snap_corner_to_center_side(
                        fp,
                        target=(prev_fp, section_center),
                        center=section_center
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

        if self.three_center_mode:
            print(f"Mode: Three-center")
            print(f"C_lower1: {self.C_lower1}, R_lower1_base: {self.R_lower1_base:.2f}mm")
            print(f"C_upper:  {self.C_upper}, R_upper_base:  {self.R_upper_base:.2f}mm")
            print(f"C_lower2: {self.C_lower2}, R_lower2_base: {self.R_lower2_base:.2f}mm")
        else:
            print(f"Mode: Single-center (legacy)")
            print(f"Center: {self.center}")
            print(f"Base Radius: {self.base_radius:.2f}mm")

        print(f"Radius Step: {self.radius_step:.2f}mm")
        print(f"Base Pitch: {self.base_pitch:.2f}mm")
        print()

        for r in range(self.rows):
            print(f"Row {r}:")
            for sec in self.sections[r]:
                if sec.type == SectionType.HORIZONTAL:
                    print(f"  {sec.type.value:12s} cols {sec.cols[0]:2d}-{sec.cols[-1]:2d} ({len(sec.cols)} keys)")
                else:
                    # Determine which radius set to use
                    if sec.type == SectionType.LOWER_ARC:
                        if sec.center == self.C_lower1:
                            R_c = self.R_center_lower1[r]
                            R_i = self.R_inner_lower1[r]
                            R_o = self.R_outer_lower1[r]
                            label = "LOWER_L"
                        else:
                            R_c = self.R_center_lower2[r]
                            R_i = self.R_inner_lower2[r]
                            R_o = self.R_outer_lower2[r]
                            label = "LOWER_R"
                    else:  # UPPER_ARC
                        R_c = self.R_center_upper[r]
                        R_i = self.R_inner_upper[r]
                        R_o = self.R_outer_upper[r]
                        label = "UPPER"

                    print(f"  {label:12s} cols {sec.cols[0]:2d}-{sec.cols[-1]:2d} ({len(sec.cols)} keys) "
                          f"R_c={R_c:.2f}mm, R_i={R_i:.2f}mm, R_o={R_o:.2f}mm")

        print(f"{'='*60}\n")
