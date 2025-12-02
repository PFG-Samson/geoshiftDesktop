import pytest
import numpy as np
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication
from ui.map_widget import MapWidget
from collections import namedtuple

# Create a simple Bounds namedtuple for testing
Bounds = namedtuple('Bounds', ['left', 'right', 'top', 'bottom'])


@pytest.fixture(scope='session')
def qapp():
    """Create QApplication instance for Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def map_widget(qapp):
    """Create a MapWidget instance for testing."""
    widget = MapWidget()
    # Mock _render_map to avoid actual rendering during tests
    widget._render_map = Mock()
    widget._show_blank_screen = Mock()
    yield widget
    widget.deleteLater()


def make_raster(name, shape=(10, 10)):
    """Helper to create a raster dict compatible with MapWidget."""
    data = np.random.randint(0, 255, size=shape, dtype=np.uint8)
    bounds = Bounds(left=-1.0, right=1.0, top=1.0, bottom=-1.0)
    
    return {
        "name": name,
        "data": data,
        "bounds": bounds,
        "preview_path": "dummy_path.png"  # Not used in comparison mode test
    }


def test_show_comparison_sets_comparison_mode(map_widget):
    """Test that show_comparison sets comparison_mode to True."""
    raster_a = make_raster("Image A")
    raster_b = make_raster("Image B")
    
    # Initially comparison_mode should be False
    assert map_widget.comparison_mode is False
    
    # Call show_comparison
    map_widget.show_comparison(raster_a, raster_b)
    
    # Verify comparison_mode is now True
    assert map_widget.comparison_mode is True
    # Verify _render_map was called
    map_widget._render_map.assert_called_once()


def test_show_comparison_adds_two_layers(map_widget):
    """Test that show_comparison adds exactly two layers."""
    raster_a = make_raster("Image A")
    raster_b = make_raster("Image B")
    
    map_widget.show_comparison(raster_a, raster_b)
    
    # Verify two layers were added
    assert len(map_widget.layers) == 2
    assert "Image A" in map_widget.layers
    assert "Image B" in map_widget.layers


def test_show_comparison_clears_existing_layers(map_widget):
    """Test that show_comparison clears any existing layers."""
    # Add a layer first
    raster_old = make_raster("Old Image")
    map_widget.add_image_layer("Old Image", raster_old, render=False)
    
    assert len(map_widget.layers) == 1
    
    # Now call show_comparison
    raster_a = make_raster("Image A")
    raster_b = make_raster("Image B")
    map_widget.show_comparison(raster_a, raster_b)
    
    # Old layer should be gone, only new layers remain
    assert len(map_widget.layers) == 2
    assert "Old Image" not in map_widget.layers
    assert "Image A" in map_widget.layers
    assert "Image B" in map_widget.layers


def test_show_comparison_handles_missing_rasters(map_widget):
    """Test that show_comparison handles None rasters gracefully."""
    # Test with None for raster_a
    map_widget.show_comparison(None, make_raster("Image B"))
    assert map_widget.comparison_mode is False
    assert len(map_widget.layers) == 0
    
    # Reset for next test
    map_widget.comparison_mode = False
    map_widget.layers.clear()
    
    # Test with None for raster_b
    map_widget.show_comparison(make_raster("Image A"), None)
    assert map_widget.comparison_mode is False
    assert len(map_widget.layers) == 0
    
    # Reset for next test
    map_widget.comparison_mode = False
    map_widget.layers.clear()
    
    # Test with both None
    map_widget.show_comparison(None, None)
    assert map_widget.comparison_mode is False
    assert len(map_widget.layers) == 0

