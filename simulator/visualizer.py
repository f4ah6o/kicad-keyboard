"""
Visualization tools for Grin array keyboard layout.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import List, Tuple
from footprint import Footprint


class GrinVisualizer:
    """Visualizes keyboard layouts."""

    def __init__(self, figsize=(12, 8)):
        """
        Initialize visualizer.

        Args:
            figsize: Figure size (width, height) in inches
        """
        self.figsize = figsize

    def plot_layout(
        self,
        footprints: List[Footprint],
        center: Tuple[float, float] = None,
        radii: List[float] = None,
        show_corners: bool = False,
        show_center: bool = True,
        title: str = "Grin Array Keyboard Layout",
        y_axis_up: bool = True,
    ):
        """
        Plot the keyboard layout.

        Args:
            footprints: List of footprints to plot
            center: Arc center point to display
            radii: List of radii to draw as reference circles
            show_corners: Whether to mark the corners of each key
            show_center: Whether to show the arc center
            title: Plot title
            y_axis_up: If False, invert Y axis so larger values are shown lower
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        # Draw reference circles if provided
        if center is not None and radii is not None:
            for r_val in radii:
                circle = plt.Circle(
                    center, r_val,
                    fill=False,
                    edgecolor='lightgray',
                    linestyle='--',
                    linewidth=1,
                    alpha=0.5
                )
                ax.add_patch(circle)

            # Draw center point
            if show_center:
                ax.plot(center[0], center[1], 'r+', markersize=10, markeredgewidth=2)
                ax.text(center[0] + 5, center[1] + 5, 'Center', fontsize=8)

        # Color map for rows
        colors = plt.cm.Set3(np.linspace(0, 1, 10))

        # Draw each footprint
        for fp in footprints:
            self._draw_footprint(ax, fp, colors[fp.row % 10], show_corners)

        # Set equal aspect ratio and labels
        ax.set_aspect('equal')
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

        if not y_axis_up:
            ax.invert_yaxis()

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=colors[i % 10], edgecolor='black', label=f'Row {i}')
            for i in range(max(fp.row for fp in footprints) + 1)
        ]
        ax.legend(handles=legend_elements, loc='upper right')

        plt.tight_layout()
        return fig, ax

    def _draw_footprint(self, ax, fp: Footprint, color: str, show_corners: bool):
        """
        Draw a single footprint.

        Args:
            ax: Matplotlib axis
            fp: Footprint to draw
            color: Fill color
            show_corners: Whether to mark corners
        """
        # Get corners
        corners = fp.get_corners()
        corner_order = ['SW', 'SE', 'NE', 'NW', 'SW']  # Close the rectangle

        # Create polygon points
        points = [corners[c] for c in corner_order]
        xs, ys = zip(*points)

        # Draw filled rectangle
        polygon = patches.Polygon(
            list(zip(xs, ys)),
            closed=True,
            edgecolor='black',
            facecolor=color,
            linewidth=1.5,
            alpha=0.7
        )
        ax.add_patch(polygon)

        # Draw center point
        ax.plot(fp.x, fp.y, 'k.', markersize=3)

        # Draw label
        label = f"R{fp.row}C{fp.col}"
        ax.text(
            fp.x, fp.y, label,
            ha='center', va='center',
            fontsize=7,
            fontweight='bold'
        )

        # Draw corners if requested
        if show_corners:
            for corner_name, (cx, cy) in corners.items():
                ax.plot(cx, cy, 'ro', markersize=3, alpha=0.5)

    def save_plot(self, filename: str):
        """Save the current plot to a file."""
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {filename}")

    def show(self):
        """Display the plot."""
        plt.show()


def plot_grin_layout(
    simulator,
    filename: str = None,
    show: bool = True,
    show_corners: bool = False
):
    """
    Convenience function to plot a Grin simulator layout.

    Args:
        simulator: GrinSimulator instance
        filename: Optional filename to save the plot
        show: Whether to display the plot
        show_corners: Whether to mark corners
    """
    visualizer = GrinVisualizer()

    fig, ax = visualizer.plot_layout(
        footprints=simulator.get_all_footprints(),
        center=simulator.center,
        radii=simulator.R,
        show_corners=show_corners,
        title=f"Grin Array Layout ({simulator.rows}×{simulator.cols})",
        y_axis_up=getattr(simulator, "y_up", True)
    )

    if filename:
        visualizer.save_plot(filename)

    if show:
        visualizer.show()

    return fig, ax
