#!/usr/bin/env python3
"""
Example usage of the Grin Array Keyboard Simulator.
"""
import json
import sys
from pathlib import Path

import numpy as np

from grin_simulator import GrinSimulator
from visualizer import plot_grin_layout

EXPORT_DIR = Path(__file__).parent / "exports"
EXPORT_DIR.mkdir(exist_ok=True)
PNG_DIR = Path(__file__).parent
DEFAULT_GAP_THRESHOLD = 0.5  # millimeters


def _footprint_snapshot(sim):
    data = []
    for fp in sim.get_all_footprints():
        data.append({
            "row": fp.row,
            "col": fp.col,
            "x": float(fp.x),
            "y": float(fp.y),
            "rotation_deg": float(np.degrees(fp.rotation)),
            "width": float(fp.width),
            "height": float(fp.height),
        })
    return data


def save_layout_snapshot(sim, example_name: str, stage: str, spacing: dict | None = None):
    payload = {
        "example": example_name,
        "stage": stage,
        "config": {
            "rows": sim.rows,
            "cols": sim.cols,
            "center": {
                "x": float(sim.center[0]),
                "y": float(sim.center[1]),
            },
            "base_radius": float(sim.base_radius),
            "radius_step": float(sim.radius_step),
            "base_pitch": float(sim.base_pitch),
            "y_up": bool(sim.y_up),
        },
        "footprints": _footprint_snapshot(sim),
    }

    if spacing is not None:
        payload["spacing"] = spacing

    export_path = EXPORT_DIR / f"{example_name}_{stage}.json"
    export_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Layout snapshot saved: {export_path}")


def print_spacing_summary(example_name: str, spacing: dict):
    print(f"Spacing summary for {example_name}:")
    print(f"  Min gap: {spacing['min_gap'] if spacing['min_gap'] is not None else 'n/a'} mm")
    print(f"  Interferences: {len(spacing['interferences'])}")
    print(f"  Small gaps (≤{DEFAULT_GAP_THRESHOLD} mm): {len(spacing['small_gaps'])}")


def export_layout_png(sim, example_name: str, stage: str, *, filename: str | None = None, show_corners: bool = False):
    """
    Save a PNG visualization for the current simulator state.
    """
    if filename is None:
        filename = PNG_DIR / f"grin_layout_{example_name}_{stage}.png"
    else:
        filename = Path(filename)

    plot_grin_layout(
        sim,
        filename=str(filename),
        show=False,
        show_corners=show_corners,
    )
    print(f"Layout PNG saved: {filename}")


def example_basic():
    """Basic example with default parameters."""
    print("=" * 60)
    print("Example 1: Basic Grin Array Layout")
    print("=" * 60)

    # Create simulator with default parameters
    sim = GrinSimulator(
        rows=3,
        cols=10,
        center=(150.0, 150.0),
        base_radius=120.0,
        radius_step=15.0,
        base_pitch=19.05,
        y_up=False,
    )

    save_layout_snapshot(sim, "basic", "initial")
    export_layout_png(sim, "basic", "initial")

    # Perform layout
    sim.layout()

    # Print summary
    sim.print_layout_summary()

    # Print some footprint positions
    print("Sample footprint positions:")
    for r in range(min(2, sim.rows)):
        for c in range(min(5, sim.cols)):
            fp = sim.footprints[r][c]
            print(f"  {fp}")

    spacing = sim.evaluate_spacing(DEFAULT_GAP_THRESHOLD)
    print_spacing_summary("Basic", spacing)
    save_layout_snapshot(sim, "basic", "final", spacing=spacing)

    # Visualize
    export_layout_png(sim, "basic", "final", filename="grin_layout_basic.png")

    return sim


def example_custom():
    """Custom example with different parameters."""
    print("\n" + "=" * 60)
    print("Example 2: Custom Grin Array Layout")
    print("=" * 60)

    # Create simulator with custom parameters
    sim = GrinSimulator(
        rows=4,
        cols=12,
        center=(200.0, 200.0),
        base_radius=150.0,
        radius_step=20.0,
        base_pitch=19.05,
        y_up=False,
    )

    save_layout_snapshot(sim, "custom", "initial")
    export_layout_png(sim, "custom", "initial")

    # Perform layout
    sim.layout()

    # Print summary
    sim.print_layout_summary()

    spacing = sim.evaluate_spacing(DEFAULT_GAP_THRESHOLD)
    print_spacing_summary("Custom", spacing)
    save_layout_snapshot(sim, "custom", "final", spacing=spacing)

    # Visualize
    export_layout_png(sim, "custom", "final", filename="grin_layout_custom.png")

    return sim


def example_compact():
    """Compact layout with smaller radius."""
    print("\n" + "=" * 60)
    print("Example 3: Compact Grin Array Layout")
    print("=" * 60)

    # Create simulator with smaller radius for tighter curve
    sim = GrinSimulator(
        rows=3,
        cols=8,
        center=(100.0, 100.0),
        base_radius=80.0,
        radius_step=12.0,
        base_pitch=19.05,
        y_up=False,
    )

    save_layout_snapshot(sim, "compact", "initial")
    export_layout_png(sim, "compact", "initial")

    # Perform layout
    sim.layout()

    # Print summary
    sim.print_layout_summary()

    spacing = sim.evaluate_spacing(DEFAULT_GAP_THRESHOLD)
    print_spacing_summary("Compact", spacing)
    save_layout_snapshot(sim, "compact", "final", spacing=spacing)

    # Visualize with corners shown
    export_layout_png(
        sim,
        "compact",
        "final",
        filename="grin_layout_compact.png",
        show_corners=True,
    )

    return sim


def example_api_demo():
    """Demonstrate the core API functions directly."""
    print("\n" + "=" * 60)
    print("Example 4: Direct API Usage")
    print("=" * 60)

    from footprint import Footprint
    from api import place_on_arc, orient_to_tangent, circle_point, angle_step
    from visualizer import GrinVisualizer

    # Create a few footprints manually
    footprints = [Footprint(row=0, col=i) for i in range(5)]

    # Define arc parameters
    center = (100.0, 100.0)
    radius = 80.0
    pitch = 19.05

    # Calculate angle step
    d_theta = angle_step(pitch, radius)
    print(f"Angle step: {np.degrees(d_theta):.2f}°")

    # Place footprints on an upper arc
    theta = -np.pi / 4  # Start at -45 degrees
    for i, fp in enumerate(footprints):
        # Place on arc
        place_on_arc(fp, center, radius, theta, y_up=False)

        # Orient to tangent
        orient_to_tangent(fp, theta, "UPPER", y_up=False)

        print(f"  Footprint {i}: pos=({fp.x:.2f}, {fp.y:.2f}), rot={np.degrees(fp.rotation):.1f}°")

        # Next angle
        theta += d_theta

    # Visualize
    vis = GrinVisualizer(figsize=(8, 8))
    fig, ax = vis.plot_layout(
        footprints,
        center=center,
        radii=[radius],
        show_corners=True,
        title="Direct API Usage - Upper Arc",
        y_axis_up=False,
    )
    vis.save_plot("grin_layout_api_demo.png")

    print("\nAPI demo complete!")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Grin Array Keyboard Simulator - Examples")
    print("=" * 60 + "\n")

    # Run examples
    try:
        example_basic()
        example_custom()
        example_compact()
        example_api_demo()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("Check the generated PNG files for visualizations.")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
