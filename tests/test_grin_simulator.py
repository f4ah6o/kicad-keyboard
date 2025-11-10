"""Tests for grin_simulator module."""
import pytest
import numpy as np
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
from grin_simulator import GrinSimulator, SectionType, Section
from visualizer import plot_grin_layout


class TestSection:
    """Test Section dataclass."""

    def test_section_creation(self):
        """Test creating a section."""
        sec = Section(type=SectionType.HORIZONTAL, cols=[0, 1, 2])
        assert sec.type == SectionType.HORIZONTAL
        assert sec.cols == [0, 1, 2]
        assert sec.theta0 == 0.0


class TestGrinSimulator:
    """Test GrinSimulator class."""

    def test_simulator_creation_basic(self):
        """Test basic simulator creation."""
        sim = GrinSimulator(rows=3, cols=5)
        assert sim.rows == 3
        assert sim.cols == 5
        assert len(sim.footprints) == 3
        assert len(sim.footprints[0]) == 5

    def test_simulator_creation_with_params(self):
        """Test simulator creation with custom parameters."""
        sim = GrinSimulator(
            rows=2,
            cols=7,
            center=(150.0, 150.0),
            base_radius=120.0,
            radius_step=15.0,
            base_pitch=20.0
        )
        assert sim.rows == 2
        assert sim.cols == 7
        assert sim.center == (150.0, 150.0)
        assert sim.base_radius == 120.0
        assert sim.radius_step == 15.0
        assert sim.base_pitch == 20.0

    def test_simulator_radius_calculation(self):
        """Test that radii decrease properly per row."""
        sim = GrinSimulator(rows=3, cols=5, base_radius=100.0, radius_step=10.0)
        assert sim.R[0] == 100.0  # Top row
        assert sim.R[1] == 90.0   # Middle row
        assert sim.R[2] == 80.0   # Bottom row

    def test_simulator_with_cols_per_row(self):
        """Test simulator with different column counts per row."""
        cols_per_row = [5, 7, 3]
        sim = GrinSimulator(rows=3, cols_per_row=cols_per_row)

        assert sim.rows == 3
        assert sim.cols_per_row == cols_per_row
        assert len(sim.footprints[0]) == 5
        assert len(sim.footprints[1]) == 7
        assert len(sim.footprints[2]) == 3

    def test_simulator_cols_per_row_mismatch(self):
        """Test that mismatched cols_per_row raises error."""
        with pytest.raises(ValueError, match="cols_per_row must match"):
            GrinSimulator(rows=3, cols_per_row=[5, 7])  # Only 2 values for 3 rows

    def test_divide_into_sections_small(self):
        """Test section division for small layouts."""
        sim = GrinSimulator(rows=1, cols=3)
        sections = sim._divide_into_sections()

        assert len(sections) == 1
        assert len(sections[0]) > 0

    def test_divide_into_sections_large(self):
        """Test section division for larger layouts."""
        sim = GrinSimulator(rows=3, cols=10)
        sections = sim._divide_into_sections()

        assert len(sections) == 3
        for row_sections in sections:
            # Should have H → L → U → L → H pattern
            assert len(row_sections) == 5
            assert row_sections[0].type == SectionType.HORIZONTAL
            assert row_sections[1].type == SectionType.LOWER_ARC
            assert row_sections[2].type == SectionType.UPPER_ARC
            assert row_sections[3].type == SectionType.LOWER_ARC
            assert row_sections[4].type == SectionType.HORIZONTAL

    def test_layout_execution(self):
        """Test that layout() executes without errors."""
        sim = GrinSimulator(rows=3, cols=10)
        sim.layout()

        # Check that footprints have been positioned
        for row in sim.footprints:
            for fp in row:
                # Position should be set (not at origin for all keys)
                assert fp.x is not None
                assert fp.y is not None

    def test_layout_spacing_evaluation(self):
        """Test that spacing evaluation works after layout."""
        sim = GrinSimulator(rows=2, cols=5, base_radius=150.0)
        sim.layout()

        spacing = sim.evaluate_spacing()
        # Just verify that spacing evaluation completes and returns valid results
        assert 'interferences' in spacing
        assert 'pairs' in spacing
        assert len(spacing['pairs']) > 0

    def test_get_all_footprints(self):
        """Test getting all footprints as flat list."""
        sim = GrinSimulator(rows=3, cols=5)
        all_fps = sim.get_all_footprints()

        assert len(all_fps) == 15  # 3 rows × 5 cols

    def test_evaluate_spacing_wrapper(self):
        """Test the convenience spacing evaluation wrapper."""
        sim = GrinSimulator(rows=2, cols=5)
        sim.layout()

        spacing = sim.evaluate_spacing(gap_threshold=1.0)

        assert 'pairs' in spacing
        assert 'interferences' in spacing
        assert 'min_gap' in spacing
        # Should have multiple pairs checked
        assert len(spacing['pairs']) > 0

    def test_print_layout_summary(self, capsys):
        """Test that layout summary prints without errors."""
        sim = GrinSimulator(rows=2, cols=5)
        sim.layout()
        sim.print_layout_summary()

        captured = capsys.readouterr()
        assert 'Grin Array Layout Summary' in captured.out
        assert 'Rows: 2' in captured.out

    def test_generate_layout_visualization(self):
        """Test generating and saving layout visualizations as PNG artifacts."""
        import matplotlib.pyplot as plt

        # Create output directory for test artifacts
        output_dir = "test-outputs"
        os.makedirs(output_dir, exist_ok=True)

        # Test case 1: Basic layout
        sim1 = GrinSimulator(rows=3, cols=10)
        sim1.layout()
        output_file1 = os.path.join(output_dir, "grin_layout_01_basic.png")
        fig1, ax1 = plot_grin_layout(sim1, filename=output_file1, show=False)
        assert os.path.exists(output_file1)
        plt.close(fig1)

        # Test case 2: Three-center mode layout
        sim2 = GrinSimulator(
            rows=3,
            cols=10,
            C_lower1=(80.0, 100.0),
            C_upper=(100.0, 100.0),
            C_lower2=(120.0, 100.0),
            R_lower1_base=150.0,
            R_upper_base=160.0,
            R_lower2_base=150.0
        )
        sim2.layout()
        output_file2 = os.path.join(output_dir, "grin_layout_02_three_center.png")
        fig2, ax2 = plot_grin_layout(sim2, filename=output_file2, show=False)
        assert os.path.exists(output_file2)
        plt.close(fig2)

        # Test case 3: Custom configuration
        sim3 = GrinSimulator(
            rows=4,
            cols=12,
            base_radius=180.0,
            radius_step=25.0,
            base_pitch=20.0
        )
        sim3.layout()
        output_file3 = os.path.join(output_dir, "grin_layout_03_custom.png")
        fig3, ax3 = plot_grin_layout(sim3, filename=output_file3, show=False)
        assert os.path.exists(output_file3)
        plt.close(fig3)

        # Test case 4: Small layout
        sim4 = GrinSimulator(rows=2, cols=5, base_radius=100.0)
        sim4.layout()
        output_file4 = os.path.join(output_dir, "grin_layout_04_small.png")
        fig4, ax4 = plot_grin_layout(sim4, filename=output_file4, show=False)
        assert os.path.exists(output_file4)
        plt.close(fig4)

        # Test case 5: Large layout
        sim5 = GrinSimulator(rows=5, cols=15, base_radius=200.0, radius_step=20.0)
        sim5.layout()
        output_file5 = os.path.join(output_dir, "grin_layout_05_large.png")
        fig5, ax5 = plot_grin_layout(sim5, filename=output_file5, show=False)
        assert os.path.exists(output_file5)
        plt.close(fig5)

        # Test case 6: Variable columns per row
        sim6 = GrinSimulator(rows=4, cols_per_row=[8, 10, 12, 10], base_radius=160.0)
        sim6.layout()
        output_file6 = os.path.join(output_dir, "grin_layout_06_variable_cols.png")
        fig6, ax6 = plot_grin_layout(sim6, filename=output_file6, show=False)
        assert os.path.exists(output_file6)
        plt.close(fig6)

        # Test case 7: Small radius layout
        sim7 = GrinSimulator(rows=3, cols=8, base_radius=80.0, radius_step=12.0)
        sim7.layout()
        output_file7 = os.path.join(output_dir, "grin_layout_07_small_radius.png")
        fig7, ax7 = plot_grin_layout(sim7, filename=output_file7, show=False)
        assert os.path.exists(output_file7)
        plt.close(fig7)

        # Test case 8: Large radius with tight pitch
        sim8 = GrinSimulator(
            rows=3,
            cols=12,
            base_radius=220.0,
            radius_step=18.0,
            base_pitch=17.0
        )
        sim8.layout()
        output_file8 = os.path.join(output_dir, "grin_layout_08_large_tight.png")
        fig8, ax8 = plot_grin_layout(sim8, filename=output_file8, show=False)
        assert os.path.exists(output_file8)
        plt.close(fig8)

        # Test case 9: Different radius steps
        sim9 = GrinSimulator(
            rows=5,
            cols=10,
            base_radius=180.0,
            radius_step=30.0,
            base_pitch=19.5
        )
        sim9.layout()
        output_file9 = os.path.join(output_dir, "grin_layout_09_large_steps.png")
        fig9, ax9 = plot_grin_layout(sim9, filename=output_file9, show=False)
        assert os.path.exists(output_file9)
        plt.close(fig9)

        # Test case 10: Complex three-center configuration
        sim10 = GrinSimulator(
            rows=4,
            cols=14,
            C_lower1=(70.0, 90.0),
            C_upper=(100.0, 110.0),
            C_lower2=(130.0, 90.0),
            R_lower1_base=140.0,
            R_upper_base=165.0,
            R_lower2_base=140.0,
            radius_step=22.0
        )
        sim10.layout()
        output_file10 = os.path.join(output_dir, "grin_layout_10_complex_three_center.png")
        fig10, ax10 = plot_grin_layout(sim10, filename=output_file10, show=False)
        assert os.path.exists(output_file10)
        plt.close(fig10)
