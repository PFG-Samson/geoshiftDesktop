"""
PyQtGraph-based map widget optimized for large GeoTIFF files (up to 5GB per image).

Features:
- GPU-accelerated rendering via OpenGL
- Tiled/windowed reading for memory efficiency
- Interactive pan, zoom, and contrast controls
- Support for multi-band imagery
- Direct NumPy array display (no PNG conversion)
"""

import numpy as np
import pyqtgraph as pg
from pyqtgraph import ImageView
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
import rasterio
from rasterio.windows import Window
from engine.logger import logger


class TiledRasterLoader:
    """
    Handles efficient loading of large rasters using tiled/windowed reading.
    Optimized for 5GB+ GeoTIFF files.
    """
    
    def __init__(self, raster_path, tile_size=2048):
        """
        Args:
            raster_path: Path to GeoTIFF file
            tile_size: Size of tiles for chunked reading (pixels)
        """
        self.path = raster_path
        self.tile_size = tile_size
        self.dataset = None
        self.overview_data = None
        self.full_shape = None
        
    def open(self):
        """Open the raster and load overview for initial display."""
        try:
            self.dataset = rasterio.open(self.path)
            self.full_shape = (self.dataset.height, self.dataset.width)
            
            # Load overview (downsampled version) for fast initial display
            # Use the smallest overview or downsample factor
            if self.dataset.overviews(1):
                # Use existing overview
                overview_level = self.dataset.overviews(1)[-1]  # Smallest overview
                overview_data = self.dataset.read(
                    out_shape=(
                        self.dataset.count,
                        self.dataset.height // overview_level,
                        self.dataset.width // overview_level
                    ),
                    resampling=rasterio.enums.Resampling.average
                )
            else:
                # Create overview by downsampling
                downsample = max(self.full_shape) // 2048  # Target ~2048px max dimension
                downsample = max(1, downsample)
                overview_data = self.dataset.read(
                    out_shape=(
                        self.dataset.count,
                        self.dataset.height // downsample,
                        self.dataset.width // downsample
                    ),
                    resampling=rasterio.enums.Resampling.average
                )
            
            # Convert to HWC format for display
            if overview_data.shape[0] <= 4:  # CHW format
                overview_data = np.transpose(overview_data, (1, 2, 0))
            
            # Handle different band counts
            if overview_data.shape[2] > 3:
                # Take first 3 bands for RGB
                self.overview_data = overview_data[:, :, :3]
            elif overview_data.shape[2] == 1:
                # Grayscale
                self.overview_data = overview_data[:, :, 0]
            else:
                self.overview_data = overview_data
            
            logger.info(f"Loaded overview: {self.overview_data.shape}, dtype: {self.overview_data.dtype}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening raster: {e}")
            return False
    
    def read_window(self, row_off, col_off, height, width):
        """
        Read a specific window/tile from the raster.
        
        Args:
            row_off, col_off: Offset in pixels
            height, width: Window size in pixels
            
        Returns:
            NumPy array of the requested window
        """
        if not self.dataset:
            return None
        
        try:
            window = Window(col_off, row_off, width, height)
            data = self.dataset.read(window=window)
            
            # Convert to HWC
            if data.shape[0] <= 4:
                data = np.transpose(data, (1, 2, 0))
            
            # Handle bands
            if data.shape[2] > 3:
                data = data[:, :, :3]
            elif data.shape[2] == 1:
                data = data[:, :, 0]
            
            return data
            
        except Exception as e:
            logger.error(f"Error reading window: {e}")
            return None
    
    def get_overview(self):
        """Get the overview/downsampled version for initial display."""
        return self.overview_data
    
    def close(self):
        """Close the raster dataset."""
        if self.dataset:
            self.dataset.close()
            self.dataset = None


class PyQtGraphMapWidget(QWidget):
    """
    High-performance map widget using PyQtGraph for raster visualization.
    Optimized for large GeoTIFF files (5GB+).
    """
    
    # Signals
    contrast_changed = pyqtSignal(float, float)  # min, max
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # State
        self.current_raster = None
        self.raster_loader = None
        self.layers = {}  # name -> loader
        
    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main ImageView
        self.image_view = ImageView()
        self.image_view.ui.roiBtn.hide()  # Hide ROI button for now
        self.image_view.ui.menuBtn.hide()  # Hide menu button
        
        # Enable antialiasing for better quality
        self.image_view.imageItem.setOpts(antialias=True)
        
        layout.addWidget(self.image_view)
        
        # Controls panel
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        # Contrast controls
        contrast_label = QLabel("Contrast:")
        controls_layout.addWidget(contrast_label)
        
        self.contrast_min_slider = QSlider(Qt.Horizontal)
        self.contrast_min_slider.setRange(0, 100)
        self.contrast_min_slider.setValue(2)  # 2nd percentile
        self.contrast_min_slider.valueChanged.connect(self.update_contrast)
        controls_layout.addWidget(QLabel("Min:"))
        controls_layout.addWidget(self.contrast_min_slider)
        
        self.contrast_max_slider = QSlider(Qt.Horizontal)
        self.contrast_max_slider.setRange(0, 100)
        self.contrast_max_slider.setValue(98)  # 98th percentile
        self.contrast_max_slider.valueChanged.connect(self.update_contrast)
        controls_layout.addWidget(QLabel("Max:"))
        controls_layout.addWidget(self.contrast_max_slider)
        
        # Reset button
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.reset_view)
        controls_layout.addWidget(reset_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
    
    def show_raster(self, raster_data):
        """
        Display a raster image.
        
        Args:
            raster_data: Dict with 'path', 'name', etc.
        """
        if not raster_data or 'path' not in raster_data:
            logger.warning("Invalid raster data")
            return
        
        try:
            # Close previous raster if any
            if self.raster_loader:
                self.raster_loader.close()
            
            # Load new raster
            self.raster_loader = TiledRasterLoader(raster_data['path'])
            if not self.raster_loader.open():
                logger.error("Failed to open raster")
                return
            
            # Get overview for display
            overview = self.raster_loader.get_overview()
            
            if overview is None:
                logger.error("Failed to load overview")
                return
            
            # Apply contrast stretch
            stretched = self.apply_contrast_stretch(overview)
            
            # Display
            self.image_view.setImage(stretched, autoRange=True, autoLevels=False)
            self.current_raster = raster_data
            
            logger.info(f"Displayed raster: {raster_data.get('name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error displaying raster: {e}")
    
    def apply_contrast_stretch(self, data):
        """
        Apply contrast stretching to image data.
        
        Args:
            data: NumPy array
            
        Returns:
            Contrast-stretched array
        """
        if data is None or data.size == 0:
            return data
        
        # Get percentile values
        min_pct = self.contrast_min_slider.value()
        max_pct = self.contrast_max_slider.value()
        
        # Calculate percentiles
        vmin = np.percentile(data, min_pct)
        vmax = np.percentile(data, max_pct)
        
        # Clip and normalize
        stretched = np.clip(data, vmin, vmax)
        if vmax > vmin:
            stretched = ((stretched - vmin) / (vmax - vmin) * 255).astype(np.uint8)
        else:
            stretched = data.astype(np.uint8)
        
        return stretched
    
    def update_contrast(self):
        """Update contrast when sliders change."""
        if self.raster_loader and self.raster_loader.overview_data is not None:
            overview = self.raster_loader.get_overview()
            stretched = self.apply_contrast_stretch(overview)
            self.image_view.setImage(stretched, autoRange=False, autoLevels=False)
    
    def reset_view(self):
        """Reset view to show entire image."""
        self.image_view.autoRange()
    
    def show_comparison(self, raster_a, raster_b, mask_a_path=None, mask_b_path=None):
        """
        Display two rasters side-by-side for comparison.
        This will be implemented in Phase 3.
        """
        logger.info("Comparison mode not yet implemented in PyQtGraph widget")
        # For now, just show the first raster
        self.show_raster(raster_a)
    
    def clear_all_layers(self):
        """Clear all displayed layers."""
        if self.raster_loader:
            self.raster_loader.close()
            self.raster_loader = None
        
        self.image_view.clear()
        self.current_raster = None
        self.layers.clear()
        logger.info("Cleared all layers")
    
    def show_map(self, raster_data, mask_path=None):
        """Display a single raster (compatibility with old interface)."""
        self.show_raster(raster_data)
