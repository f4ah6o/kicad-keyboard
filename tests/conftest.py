"""Pytest configuration and shared fixtures."""
import sys
from pathlib import Path

# Add simulator directory to path
simulator_path = Path(__file__).parent.parent / "simulator"
sys.path.insert(0, str(simulator_path))
