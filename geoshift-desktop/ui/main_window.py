import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QSplitter, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QFileDialog, QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ui.map_widget import MapWidget
from ui.symbology_panel import SymbologyPanel
from ui.layer_panel import LayerPanel
from ui.dialogs.open_file_dialog import open_file_dialog
from engine.reader import load_raster
from engine.analysis_change import run_detection
from engine.change_tools import calculate_change_area, generate_change_map
from engine.exporter import export_report
from engine.models_manager import get_models_manager
from engine.logger import logger
from app import AppState
import numpy as np
from PIL import Image
import rasterio
import cv2

class RasterLoader(QThread):
    """Thread for loading rasters without blocking UI."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, path):
        super().__init__()
        self.path = path
    
    def run(self):
        try:
            data = load_raster(self.path)
            if data:
                self.finished.emit(data)
            else:
                self.error.emit("Failed to load raster")
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Geoshift Desktop - Change Detection Platform")
        self.resize(1280, 850)
        
        self.state = AppState()
        self.models_manager = get_models_manager()
        
        # Main Layout
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #f5f6fa;")
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. Top Toolbar
        self.setup_top_toolbar()
        
        # Content Area (Sidebar + Map)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.main_layout.addWidget(content_widget)
        
        # 2. Left Sidebar (Tools & Symbology)
        self.setup_sidebar()
        content_layout.addWidget(self.sidebar)
        
        # 3. Map Area (Center)
        map_container = QWidget()
        map_container_layout = QVBoxLayout(map_container)
        map_container_layout.setContentsMargins(0, 0, 0, 0)
        map_container_layout.setSpacing(0)
        
        # Comparison mode indicator (initially hidden)
        self.comparison_indicator = QLabel("💡 Drag the slider to compare images side-by-side")
        self.comparison_indicator.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 13px;
            }
        """)
        self.comparison_indicator.setAlignment(Qt.AlignCenter)
        self.comparison_indicator.hide()  # Hidden by default
        
        map_container_layout.addWidget(self.comparison_indicator)
        self.map_widget = MapWidget()
        map_container_layout.addWidget(self.map_widget, stretch=1)
        
        content_layout.addWidget(map_container, stretch=1)
        
        # 4. Right Sidebar (Layers)
        self.setup_layer_panel()
        content_layout.addWidget(self.layer_panel)
        
        # 4. Bottom Panel
        self.setup_bottom_panel()
        self.main_layout.addWidget(self.bottom_panel)
        
        # Connect Signals
        self.btn_load_a.clicked.connect(lambda: self.load_image('A'))
        self.btn_load_b.clicked.connect(lambda: self.load_image('B'))
        self.btn_analyze.clicked.connect(self.run_analysis)
        self.btn_toggle_change.clicked.connect(self.toggle_change)
        self.btn_export.clicked.connect(self.export_report)
        
        # Symbology signals
        self.symbology_panel.opacity_changed.connect(self.on_opacity_changed)
        self.symbology_panel.brightness_changed.connect(self.on_brightness_changed)
        self.symbology_panel.contrast_changed.connect(self.on_contrast_changed)
        
        # Layer Panel signals
        self.layer_panel.visibility_changed.connect(self.map_widget.toggle_layer_visibility)
        self.layer_panel.layer_removed.connect(self.map_widget.remove_layer)
        self.layer_panel.layer_selected.connect(self.on_layer_selected)
        
        # Initial UI State
        self.update_ui_state()

    def setup_top_toolbar(self):
        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(60)
        self.top_bar.setStyleSheet("""
            background-color: #ffffff;
            border-bottom: 1px solid #dcdde1;
        """)
        layout = QHBoxLayout(self.top_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # Branding
        brand_label = QLabel("GEOSHIFT")
        brand_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(brand_label)
        
        subtitle = QLabel(" |  Change Detection Platform")
        subtitle.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-top: 4px;")
        layout.addWidget(subtitle)
        
        layout.addStretch()
        
        # Toolbar Actions
        # User requested to remove Load A/B from here to avoid duplication with sidebar
        
        btn_swap = QPushButton("🔄 Swap")
        btn_swap.setToolTip("Swap Image A and Image B positions in the comparison view (left ↔ right).")
        btn_swap.clicked.connect(self.swap_layers)
        self._style_toolbar_btn(btn_swap)
        layout.addWidget(btn_swap)

        btn_clear = QPushButton("🗑️ Clear All")
        btn_clear.setToolTip("Remove all loaded images and reset the application to its initial state.")
        btn_clear.clicked.connect(self.clear_all_layers)
        self._style_toolbar_btn(btn_clear)
        layout.addWidget(btn_clear)

        layout.addStretch()
        
        # Add to main layout immediately to ensure it's at the top
        self.main_layout.addWidget(self.top_bar)

    def _style_toolbar_btn(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                border: none;
                color: #57606f;
                padding: 6px 12px;
                font-weight: 600;
                background: #f1f2f6;
                border-radius: 4px;
                margin-right: 8px;
            }
            QPushButton:hover {
                color: #2f3542;
                background-color: #dfe4ea;
            }
        """)

    def setup_layer_panel(self):
        self.layer_panel = LayerPanel(self.map_widget)

    def setup_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(300)
        self.sidebar.setStyleSheet("background-color: #ffffff; border-right: 1px solid #dcdde1;")
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(20)
        
        # Section 1: Images
        self.btn_load_a = self.create_button("Load Image A (Before)", "primary")
        self.btn_load_a.setToolTip("Load the 'before' image for comparison. Supports GeoTIFF, PNG, JPEG formats.")
        self.btn_load_b = self.create_button("Load Image B (After)", "primary")
        self.btn_load_b.setToolTip("Load the 'after' image for comparison. Images will be displayed side-by-side with an interactive slider.")
        
        images_layout = QVBoxLayout()
        images_layout.addWidget(self.btn_load_a)
        images_layout.addWidget(self.btn_load_b)
        self.create_sidebar_section(layout, "IMAGES", images_layout)
        
        # Section 2: Analysis
        analysis_layout = QVBoxLayout()
        
        type_label = QLabel("Detection Type")
        type_label.setStyleSheet("color: #7f8c8d; font-size: 11px; font-weight: 600; margin-bottom: 5px;")
        analysis_layout.addWidget(type_label)
        
        self.analysis_combo = QComboBox()
        self.analysis_combo.addItems(["Land-use Change", "Deforestation", "Water Change", "New Structures", "Disaster Damage"])
        # Map friendly names to internal keys
        self.analysis_combo.setItemData(0, "landuse")
        self.analysis_combo.setItemData(1, "deforestation")
        self.analysis_combo.setItemData(2, "water")
        self.analysis_combo.setItemData(3, "structures")
        self.analysis_combo.setItemData(4, "disaster")
        
        self.analysis_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #dcdde1;
                border-radius: 4px;
                background: #f8f9fa;
                color: #2c3e50;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.analysis_combo.setToolTip("Select the type of change detection analysis to perform on the loaded images.")
        self.analysis_combo.currentIndexChanged.connect(self.on_analysis_type_changed)
        analysis_layout.addWidget(self.analysis_combo)
        
        self.btn_analyze = self.create_button("Run Analysis", "action")
        self.btn_analyze.setToolTip("Run change detection analysis on both loaded images. Results will be displayed as a colored overlay.")
        self.btn_toggle_change = self.create_button("Toggle Overlay", "secondary")
        self.btn_toggle_change.setToolTip("Show or hide the change detection overlay on the comparison view.")
        self.btn_export = self.create_button("Export Report", "secondary")
        self.btn_export.setToolTip("Export analysis results as an HTML report with statistics and visualizations.")
        
        analysis_layout.addSpacing(10)
        analysis_layout.addWidget(self.btn_analyze)
        analysis_layout.addWidget(self.btn_toggle_change)
        analysis_layout.addWidget(self.btn_export)
        
        self.create_sidebar_section(layout, "ANALYSIS", analysis_layout)
        
        # Section 3: Symbology
        self.symbology_panel = SymbologyPanel()
        # Wrap symbology panel in a layout to pass to create_sidebar_section
        sym_layout = QVBoxLayout()
        sym_layout.addWidget(self.symbology_panel)
        self.create_sidebar_section(layout, "SYMBOLOGY", sym_layout)
        
        layout.addStretch()

    def create_sidebar_section(self, parent_layout, title, content_layout):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e1e4e8;
                border-radius: 8px;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        
        header = QLabel(title)
        header.setStyleSheet("color: #95a5a6; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none;")
        frame_layout.addWidget(header)
        frame_layout.addSpacing(5)
        
        frame_layout.addLayout(content_layout)
        parent_layout.addWidget(frame)

    def setup_bottom_panel(self):
        self.bottom_panel = QWidget()
        self.bottom_panel.setFixedHeight(40)
        self.bottom_panel.setStyleSheet("background-color: #2c3e50; color: white;")
        layout = QHBoxLayout(self.bottom_panel)
        layout.setContentsMargins(15, 0, 15, 0)
        
        self.log_label = QLabel("Ready")
        self.log_label.setStyleSheet("font-weight: 500;")
        layout.addWidget(self.log_label)
        
        layout.addStretch()
        
        # Compact Metadata
        self.meta_label = QLabel("")
        self.meta_label.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        layout.addWidget(self.meta_label)

    def create_button(self, text, style="secondary"):
        btn = QPushButton(text)
        
        base_style = """
            QPushButton {
                padding: 10px;
                border-radius: 4px;
                font-weight: 500;
                text-align: center;
            }
        """
        
        if style == "primary":
            color_style = """
                QPushButton {
                    background-color: #ecf0f1;
                    color: #2c3e50;
                    border: 1px solid #bdc3c7;
                    text-align: left;
                }
                QPushButton:hover { background-color: #dfe6e9; }
                QPushButton:disabled { color: #bdc3c7; }
            """
        elif style == "action":
            color_style = """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #2980b9; }
                QPushButton:disabled { background-color: #95a5a6; }
            """
        else: # secondary
            color_style = """
                QPushButton {
                    background-color: transparent;
                    color: #2c3e50;
                    border: 1px solid #bdc3c7;
                }
                QPushButton:hover { background-color: #f5f6fa; }
                QPushButton:disabled { color: #bdc3c7; border-color: #ecf0f1; }
            """
            
        btn.setStyleSheet(base_style + color_style)
        return btn

    def log(self, message):
        self.log_label.setText(message)
        logger.info(message)

    def update_ui_state(self):
        has_both = self.state.has_both_images()
        self.btn_analyze.setEnabled(has_both)
        self.btn_toggle_change.setEnabled(self.state.change_mask is not None)
        self.btn_export.setEnabled(self.state.change_results is not None)

    def update_metadata(self, data, slot):
        """Update compact metadata label."""
        if not data:
            return
        
        filename = os.path.basename(data.get('path', ''))
        dims = f"{data['width']}x{data['height']}"
        crs = str(data['crs'])
        
        current_text = self.meta_label.text()
        new_info = f"Img {slot}: {filename} ({dims}, {crs})"
        
        if current_text:
            self.meta_label.setText(f"{current_text}  |  {new_info}")
        else:
            self.meta_label.setText(new_info)

    def load_image(self, slot):
        logger.info(f"load_image called for slot {slot}")
        path = open_file_dialog(self, f"Open Image {slot}")
        if path:
            logger.info(f"Selected file: {path}")
            self.log(f"Loading Image {slot}: {os.path.basename(path)}...")
            if slot == 'A':
                self.btn_load_a.setEnabled(False)
            else:
                self.btn_load_b.setEnabled(False)
            
            loader = RasterLoader(path)
            loader.finished.connect(lambda data: self.on_raster_loaded(data, slot))
            loader.error.connect(lambda err: self.on_raster_error(err, slot))
            loader.start()
            if slot == 'A':
                self.current_loader_a = loader
            else:
                self.current_loader_b = loader
    
    def on_raster_loaded(self, data, slot):
        """Callback when raster loading completes."""
        logger.info(f"Raster loaded for slot {slot}: {data.get('path', 'unknown')}")
        if slot == 'A':
            self.state.raster_a = data
            self.log(f"Loaded Image A: {os.path.basename(data['path'])}")
            self.btn_load_a.setEnabled(True)
            self.update_metadata(data, 'A')
        elif slot == 'B':
            self.state.raster_b = data
            self.log(f"Loaded Image B: {os.path.basename(data['path'])}")
            self.btn_load_b.setEnabled(True)
            self.update_metadata(data, 'B')
        
        # Show comparison if both loaded
        if self.state.has_both_images():
            self.refresh_comparison()
            self.log("Both images loaded. Select analysis type and click 'Run Analysis'.")
            # Show comparison mode indicator
            self.comparison_indicator.show()
        else:
            # Show single image
            self.map_widget.show_map(data)
            # Hide comparison indicator
            self.comparison_indicator.hide()
        
        self.layer_panel.refresh()
        self.update_ui_state()
    
    def on_raster_error(self, error, slot):
        """Callback when raster loading fails."""
        logger.error(f"Error loading Image {slot}: {error}")
        self.log(f"Error loading Image {slot}: {error}")
        if slot == 'A':
            self.btn_load_a.setEnabled(True)
        else:
            self.btn_load_b.setEnabled(True)
    
    def on_analysis_type_changed(self, index):
        """Update selected analysis type."""
        self.state.selected_analysis_type = self.analysis_combo.itemData(index)
        self.log(f"Analysis type: {self.analysis_combo.currentText()}")
    
    def refresh_comparison(self):
        """Refresh the comparison view."""
        change_mask_path = "change_mask.png" if self.state.change_mask is not None and self.state.change_visible else None
        self.map_widget.show_comparison(
            self.state.raster_a, 
            self.state.raster_b,
            change_mask_path,
            change_mask_path  # Show on both sides
        )
        self.layer_panel.refresh()

    def run_analysis(self):
        logger.info("run_analysis called")
        if not self.state.has_both_images():
            logger.warning("Cannot run analysis: missing images")
            return
        
        analysis_type = self.state.selected_analysis_type
        logger.info(f"Starting analysis: {analysis_type}")
        self.log(f"Running {self.analysis_combo.currentText()}...")
        self.btn_analyze.setEnabled(False)
        
        try:
            # Read full images
            with rasterio.open(self.state.raster_a['path']) as src_a:
                img_a = src_a.read()
                # Convert to HWC format for OpenCV
                if img_a.shape[0] <= 4:  # CHW format
                    img_a = np.transpose(img_a, (1, 2, 0))
                if img_a.shape[2] > 3:
                    img_a = img_a[:, :, :3]  # Take first 3 bands
            
            with rasterio.open(self.state.raster_b['path']) as src_b:
                img_b = src_b.read()
                if img_b.shape[0] <= 4:
                    img_b = np.transpose(img_b, (1, 2, 0))
                if img_b.shape[2] > 3:
                    img_b = img_b[:, :, :3]
            
            # Ensure images are 3-channel for OpenCV processing
            if img_a.ndim == 2:
                img_a = cv2.cvtColor(img_a, cv2.COLOR_GRAY2RGB)
            elif img_a.shape[2] == 1:
                img_a = cv2.cvtColor(img_a, cv2.COLOR_GRAY2RGB)
            if img_b.ndim == 2:
                img_b = cv2.cvtColor(img_b, cv2.COLOR_GRAY2RGB)
            elif img_b.shape[2] == 1:
                img_b = cv2.cvtColor(img_b, cv2.COLOR_GRAY2RGB)
            
            # Ensure both images have the same dimensions
            if img_a.shape[:2] != img_b.shape[:2]:
                self.log(f"Resizing images to match dimensions...")
                # Resize to the smaller dimensions to preserve quality
                target_height = min(img_a.shape[0], img_b.shape[0])
                target_width = min(img_a.shape[1], img_b.shape[1])
                
                if img_a.shape[:2] != (target_height, target_width):
                    img_a = cv2.resize(img_a, (target_width, target_height), interpolation=cv2.INTER_AREA)
                    self.log(f"Resized Image A to {target_width}x{target_height}")
                
                if img_b.shape[:2] != (target_height, target_width):
                    img_b = cv2.resize(img_b, (target_width, target_height), interpolation=cv2.INTER_AREA)
                    self.log(f"Resized Image B to {target_width}x{target_height}")
            
            # Run detection
            change_mask, stats = run_detection(img_a, img_b, analysis_type)
            
            self.state.change_mask = change_mask
            self.state.change_results = stats
            
            # Save change mask as colored overlay
            change_colored = generate_change_map(change_mask, change_mask)
            change_img = Image.fromarray(change_colored, mode='RGB')
            
            # Make semi-transparent
            change_rgba = Image.new("RGBA", change_img.size)
            change_rgba.paste(change_img)
            
            # Apply transparency where no change
            pixels = change_rgba.load()
            for i in range(change_rgba.size[0]):
                for j in range(change_rgba.size[1]):
                    if pixels[i, j][:3] == (0, 0, 0):  # No change
                        pixels[i, j] = (0, 0, 0, 0)
                    else:
                        pixels[i, j] = (*pixels[i, j][:3], 180)
            
            change_rgba.save("change_mask.png")
            
            self.refresh_comparison()
            
            change_pct = stats.get('change_percentage', 0)
            self.log(f"Analysis complete. Change detected: {change_pct:.2f}% of image area.")
            
        except Exception as e:
            self.log(f"Analysis error: {e}")
        finally:
            self.btn_analyze.setEnabled(True)
            self.update_ui_state()

    def toggle_change(self):
        if self.state.change_mask is not None:
            self.state.change_visible = not self.state.change_visible
            self.refresh_comparison()

    def export_report(self):
        if self.state.change_results:
            path, _ = QFileDialog.getSaveFileName(self, "Save Report", "change_report.html", "HTML Files (*.html)")
            if path:
                data = {
                    **self.state.change_results,
                    "analysis_type": self.analysis_combo.currentText(),
                    "image_a": os.path.basename(self.state.raster_a['path']),
                    "image_b": os.path.basename(self.state.raster_b['path']),
                    "preview_a": self.state.raster_a['preview_path'],
                    "preview_b": self.state.raster_b['preview_path']
                }
                success = export_report(data, path)
                if success:
                    QMessageBox.information(self, "Success", "Report exported successfully.")
                else:
                    QMessageBox.critical(self, "Error", "Failed to export report.")
    
    def on_opacity_changed(self, value):
        """Handle opacity adjustment from symbology panel."""
        # Update currently selected layer if any
        if hasattr(self, 'selected_layer') and self.selected_layer:
            # We need to update the layer in map_widget
            # But map_widget.layers stores info. We need a method to update opacity.
            # For now, let's just re-add the layer with new opacity or update the dict and re-render
            if self.selected_layer in self.map_widget.layers:
                self.map_widget.layers[self.selected_layer]['opacity'] = value
                self.map_widget._render_map()
    
    def on_brightness_changed(self, value):
        """Handle brightness adjustment from symbology panel."""
        # TODO: Implement brightness adjustment (requires raster processing or CSS filter)
        pass
    
    def on_contrast_changed(self, value):
        """Handle contrast adjustment from symbology panel."""
        # TODO: Implement contrast adjustment
        pass

    def on_layer_selected(self, name):
        """Handle layer selection from LayerPanel."""
        self.selected_layer = name
        # Update symbology panel to reflect this layer's settings if we stored them
        # For now, just reset or keep current
        self.log(f"Selected layer: {name}")

    def swap_layers(self):
        """Swap Image A and Image B."""
        if self.state.has_both_images():
            self.state.raster_a, self.state.raster_b = self.state.raster_b, self.state.raster_a
            self.refresh_comparison()
            self.log("Swapped Image A and Image B")
            # Update metadata labels
            self.update_metadata(self.state.raster_a, 'A')
            self.update_metadata(self.state.raster_b, 'B')

    def clear_all_layers(self):
        self.map_widget.clear_all_layers()
        self.layer_panel.refresh()
        self.state.raster_a = None
        self.state.raster_b = None
        self.btn_load_a.setEnabled(True)
        self.btn_load_b.setEnabled(True)
        self.meta_label.setText("")
        self.comparison_indicator.hide()  # Hide indicator when clearing
        self.log("Cleared all layers")
