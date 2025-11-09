"""Tests for visualizer module."""
import pytest
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt
from footprint import Footprint
from visualizer import GrinVisualizer, plot_grin_layout
from grin_simulator import GrinSimulator


class TestGrinVisualizer:
    """Test GrinVisualizer class."""

    def test_visualizer_creation(self):
        """Test creating a visualizer."""
        viz = GrinVisualizer(figsize=(10, 8))
        assert viz.figsize == (10, 8)

    def test_plot_layout_basic(self):
        """Test plotting a basic layout."""
        viz = GrinVisualizer()

        # Create some test footprints
        footprints = [
            Footprint(row=0, col=0, x=0.0, y=0.0),
            Footprint(row=0, col=1, x=20.0, y=0.0),
            Footprint(row=1, col=0, x=0.0, y=20.0),
        ]

        fig, ax = viz.plot_layout(footprints)

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_layout_with_center(self):
        """Test plotting layout with center point."""
        viz = GrinVisualizer()

        footprints = [
            Footprint(row=0, col=0, x=0.0, y=0.0),
        ]

        fig, ax = viz.plot_layout(
            footprints,
            center=(100.0, 100.0),
            radii=[50.0, 100.0],
            show_center=True
        )

        assert fig is not None
        plt.close(fig)

    def test_plot_layout_with_corners(self):
        """Test plotting layout with corners shown."""
        viz = GrinVisualizer()

        footprints = [
            Footprint(row=0, col=0, x=0.0, y=0.0),
        ]

        fig, ax = viz.plot_layout(
            footprints,
            show_corners=True
        )

        assert fig is not None
        plt.close(fig)

    def test_plot_layout_inverted_y(self):
        """Test plotting with inverted Y axis."""
        viz = GrinVisualizer()

        footprints = [
            Footprint(row=0, col=0, x=0.0, y=0.0),
        ]

        fig, ax = viz.plot_layout(
            footprints,
            y_axis_up=False
        )

        assert fig is not None
        # Check that Y axis is inverted
        ylim = ax.get_ylim()
        assert ylim[0] > ylim[1]  # Inverted means top > bottom
        plt.close(fig)

    def test_save_plot(self, tmp_path):
        """Test saving plot to file."""
        viz = GrinVisualizer()

        footprints = [
            Footprint(row=0, col=0, x=0.0, y=0.0),
        ]

        fig, ax = viz.plot_layout(footprints)

        # Save to temporary file
        output_file = tmp_path / "test_plot.png"
        viz.save_plot(str(output_file))

        assert output_file.exists()
        plt.close(fig)


class TestPlotGrinLayout:
    """Test convenience function for plotting Grin layouts."""

    def test_plot_grin_layout_basic(self):
        """Test plotting a Grin simulator layout."""
        sim = GrinSimulator(rows=2, cols=3)
        sim.layout()

        fig, ax = plot_grin_layout(sim, show=False)

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_grin_layout_with_file(self, tmp_path):
        """Test plotting and saving to file."""
        sim = GrinSimulator(rows=2, cols=3)
        sim.layout()

        output_file = tmp_path / "grin_layout.png"
        fig, ax = plot_grin_layout(sim, filename=str(output_file), show=False)

        assert output_file.exists()
        plt.close(fig)

    def test_plot_grin_layout_with_corners(self):
        """Test plotting with corners visible."""
        sim = GrinSimulator(rows=2, cols=3)
        sim.layout()

        fig, ax = plot_grin_layout(sim, show_corners=True, show=False)

        assert fig is not None
        plt.close(fig)
