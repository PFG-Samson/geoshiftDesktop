"""
Side-by-side comparison widget for PyQtGraph.
Displays two rasters with synchronized pan/zoom and an interactive slider.
"""

import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
                             QLabel, QSlider, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.pyqtgraph_map_widget import TiledRasterLoader
from engine.logger import logger


class SynchronizedImageView(pg.ImageView):
    """ImageView with signals for pan/zoom synchronization."""
    
    view_changed = pyqtSignal(object)  # Emits view range
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view.sigRangeChanged.connect(self.on_range_changed)
        self._updating = False
    
    def on_range_changed(self):
        """Emit signal when view range changes."""
        if not self._updating:
            self.view_changed.emit(self.view.viewRange())
    
    def set_view_range(self, range_data):
        """Set view range from another view."""
        self._updating = True
        self.view.setRange(xRange=range_data[0], yRange=range_data[1], padding=0)
        self._updating = False


class ComparisonWidget(QWidget):
    """
    Widget for side-by-side raster comparison with synchronized pan/zoom.
    Optimized for large GeoTIFF files (5GB+).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # State
        self.loader_a = None
        self.loader_b = None
        self.sync_enabled = True
        
    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top controls
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        # Labels
        self.label_a = QLabel("Image A (Before)")
        self.label_a.setStyleSheet("font-weight: bold; color: #3498db;")
        controls_layout.addWidget(self.label_a)
        
        controls_layout.addStretch()
        
        # Sync toggle
        self.sync_btn = QPushButton("🔗 Sync Pan/Zoom")
        self.sync_btn.setCheckable(True)
        self.sync_btn.setChecked(True)
        self.sync_btn.clicked.connect(self.toggle_sync)
        self.sync_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border-radius: 3px;
                background: #3498db;
                color: white;
                font-weight: 500;
            }
            QPushButton:checked {
                background: #2ecc71;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        controls_layout.addWidget(self.sync_btn)
        
        controls_layout.addStretch()
        
        self.label_b = QLabel("Image B (After)")
        self.label_b.setStyleSheet("font-weight: bold; color: #e74c3c;")
        controls_layout.addWidget(self.label_b)
        
        layout.addLayout(controls_layout)
        
        # Splitter for side-by-side views
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left image view
        self.view_a = SynchronizedImageView()
        self.view_a.ui.roiBtn.hide()
        self.view_a.ui.menuBtn.hide()
        self.view_a.imageItem.setOpts(antialias=True)
        self.view_a.view_changed.connect(self.on_view_a_changed)
        
        # Right image view
        self.view_b = SynchronizedImageView()
        self.view_b.ui.roiBtn.hide()
        self.view_b.ui.menuBtn.hide()
        self.view_b.imageItem.setOpts(antialias=True)
        self.view_b.view_changed.connect(self.on_view_b_changed)
        
        self.splitter.addWidget(self.view_a)
        self.splitter.addWidget(self.view_b)
        self.splitter.setSizes([500, 500])  # Equal split
        
        layout.addWidget(self.splitter)
        
        # Bottom controls
        bottom_controls = QHBoxLayout()
        bottom_controls.setContentsMargins(10, 5, 10, 5)
        
        # Contrast controls for both images
        bottom_controls.addWidget(QLabel("Contrast:"))
        
        self.contrast_min = QSlider(Qt.Horizontal)
        self.contrast_min.setRange(0, 100)
        self.contrast_min.setValue(2)
        self.contrast_min.valueChanged.connect(self.update_contrast)
        bottom_controls.addWidget(QLabel("Min:"))
        bottom_controls.addWidget(self.contrast_min)
        
        self.contrast_max = QSlider(Qt.Horizontal)
        self.contrast_max.setRange(0, 100)
        self.contrast_max.setValue(98)
        self.contrast_max.valueChanged.connect(self.update_contrast)
        bottom_controls.addWidget(QLabel("Max:"))
        bottom_controls.addWidget(self.contrast_max)
        
        # Reset button
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.reset_view)
        bottom_controls.addWidget(reset_btn)
        
        bottom_controls.addStretch()
        layout.addLayout(bottom_controls)
    
    def show_comparison(self, raster_a, raster_b, mask_a_path=None, mask_b_path=None):
        """
        Display two rasters side-by-side.
        
        Args:
            raster_a: Dict with 'path', 'name', etc. for first image
            raster_b: Dict with 'path', 'name', etc. for second image
            mask_a_path: Optional path to mask for image A
            mask_b_path: Optional path to mask for image B
        """
        if not raster_a or not raster_b:
            logger.warning("Missing raster data for comparison")
            return
        
        try:
            # Close previous loaders
            if self.loader_a:
                self.loader_a.close()
            if self.loader_b:
                self.loader_b.close()
            
            # Load raster A
            self.loader_a = TiledRasterLoader(raster_a['path'])
            if not self.loader_a.open():
                logger.error("Failed to open raster A")
                return
            
            # Load raster B
            self.loader_b = TiledRasterLoader(raster_b['path'])
            if not self.loader_b.open():
                logger.error("Failed to open raster B")
                return
            
            # Get overviews
            overview_a = self.loader_a.get_overview()
            overview_b = self.loader_b.get_overview()
            
            if overview_a is None or overview_b is None:
                logger.error("Failed to load overviews")
                return
            
            # Apply contrast stretch
            stretched_a = self.apply_contrast_stretch(overview_a)
            stretched_b = self.apply_contrast_stretch(overview_b)
            
            # Display
            self.view_a.setImage(stretched_a, autoRange=True, autoLevels=False)
            self.view_b.setImage(stretched_b, autoRange=True, autoLevels=False)
            
            # Update labels
            self.label_a.setText(f"Image A: {raster_a.get('name', 'Unknown')}")
            self.label_b.setText(f"Image B: {raster_b.get('name', 'Unknown')}")
            
            logger.info("Comparison view loaded successfully")
            
        except Exception as e:
            logger.error(f"Error in comparison view: {e}")
    
    def apply_contrast_stretch(self, data):
        """Apply contrast stretching to image data."""
        if data is None or data.size == 0:
            return data
        
        min_pct = self.contrast_min.value()
        max_pct = self.contrast_max.value()
        
        vmin = np.percentile(data, min_pct)
        vmax = np.percentile(data, max_pct)
        
        stretched = np.clip(data, vmin, vmax)
        if vmax > vmin:
            stretched = ((stretched - vmin) / (vmax - vmin) * 255).astype(np.uint8)
        else:
            stretched = data.astype(np.uint8)
        
        return stretched
    
    def update_contrast(self):
        """Update contrast for both images."""
        if self.loader_a and self.loader_a.overview_data is not None:
            overview_a = self.loader_a.get_overview()
            stretched_a = self.apply_contrast_stretch(overview_a)
            self.view_a.setImage(stretched_a, autoRange=False, autoLevels=False)
        
        if self.loader_b and self.loader_b.overview_data is not None:
            overview_b = self.loader_b.get_overview()
            stretched_b = self.apply_contrast_stretch(overview_b)
            self.view_b.setImage(stretched_b, autoRange=False, autoLevels=False)
    
    def on_view_a_changed(self, range_data):
        """Sync view B when view A changes."""
        if self.sync_enabled:
            self.view_b.set_view_range(range_data)
    
    def on_view_b_changed(self, range_data):
        """Sync view A when view B changes."""
        if self.sync_enabled:
            self.view_a.set_view_range(range_data)
    
    def toggle_sync(self):
        """Toggle pan/zoom synchronization."""
        self.sync_enabled = self.sync_btn.isChecked()
        if self.sync_enabled:
            self.sync_btn.setText("🔗 Sync Pan/Zoom")
            # Sync to view A's current range
            self.view_b.set_view_range(self.view_a.view.viewRange())
        else:
            self.sync_btn.setText("🔓 Independent")
    
    def reset_view(self):
        """Reset both views to show entire images."""
        self.view_a.autoRange()
        self.view_b.autoRange()
    
    def clear(self):
        """Clear both views."""
        if self.loader_a:
            self.loader_a.close()
            self.loader_a = None
        if self.loader_b:
            self.loader_b.close()
            self.loader_b = None
        
        self.view_a.clear()
        self.view_b.clear()
        logger.info("Cleared comparison views")
