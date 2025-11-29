import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QSplitter, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QFileDialog, QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ui.map_widget import MapWidget
from ui.symbology_panel import SymbologyPanel
from ui.dialogs.open_file_dialog import open_file_dialog
from core.reader import load_raster
from core.analysis_change import run_detection
from core.change_tools import calculate_change_area, generate_change_map
from core.exporter import export_report
from core.models_manager import get_models_manager
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
        self.resize(1200, 800)
        
        self.state = AppState()
        self.models_manager = get_models_manager()
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setStyleSheet("background-color: #2c3e50; color: white;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        # Branding
        title_label = QLabel("GEOSHIFT")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Change Detection Platform")
        subtitle_label.setStyleSheet("font-size: 12px; margin-bottom: 20px; color: #95a5a6;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(subtitle_label)
        
        # Image Loading Section
        section_label = QLabel("IMAGES")
        section_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #95a5a6; margin-top: 10px;")
        sidebar_layout.addWidget(section_label)
        
        self.btn_load_a = self.create_button("Load Image A (Before)")
        self.btn_load_b = self.create_button("Load Image B (After)")
        
        sidebar_layout.addWidget(self.btn_load_a)
        sidebar_layout.addWidget(self.btn_load_b)
        
        # Analysis Section
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #34495e; margin: 15px 0;")
        sidebar_layout.addWidget(line)
        
        section_label2 = QLabel("ANALYSIS")
        section_label2.setStyleSheet("font-size: 11px; font-weight: bold; color: #95a5a6;")
        sidebar_layout.addWidget(section_label2)
        
        # Analysis Type Dropdown
        type_label = QLabel("Detection Type:")
        type_label.setStyleSheet("font-size: 12px; margin-top: 10px;")
        sidebar_layout.addWidget(type_label)
        
        self.analysis_combo = QComboBox()
        self.analysis_combo.addItem("Land-use Change", "landuse")
        self.analysis_combo.addItem("Deforestation", "deforestation")
        self.analysis_combo.addItem("Water Change", "water")
        self.analysis_combo.addItem("New Structures", "structures")
        self.analysis_combo.addItem("Disaster Damage", "disaster")
        self.analysis_combo.setStyleSheet("""
            QComboBox {
                background-color: #34495e;
                border: none;
                padding: 8px;
                color: white;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #34495e;
                color: white;
                selection-background-color: #2980b9;
            }
        """)
        self.analysis_combo.currentIndexChanged.connect(self.on_analysis_type_changed)
        sidebar_layout.addWidget(self.analysis_combo)
        
        self.btn_analyze = self.create_button("Run Analysis")
        self.btn_toggle_change = self.create_button("Toggle Change Overlay")
        self.btn_export = self.create_button("Export Report")
        
        sidebar_layout.addWidget(self.btn_analyze)
        sidebar_layout.addWidget(self.btn_toggle_change)
        sidebar_layout.addWidget(self.btn_export)
        
        # Symbology Section
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        line2.setStyleSheet("background-color: #34495e; margin: 15px 0;")
        sidebar_layout.addWidget(line2)
        
        self.symbology_panel = SymbologyPanel()
        sidebar_layout.addWidget(self.symbology_panel)
        
        sidebar_layout.addStretch()
        
        # Main Content Area
        content_splitter = QSplitter(Qt.Vertical)
        
        # Map
        self.map_widget = MapWidget()
        content_splitter.addWidget(self.map_widget)
        
        # Bottom Panel
        self.bottom_panel = QWidget()
        self.bottom_panel.setFixedHeight(200)
        bottom_layout = QHBoxLayout(self.bottom_panel)
        
        # Metadata Table
        self.meta_table = QTableWidget()
        self.meta_table.setColumnCount(2)
        self.meta_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.meta_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        bottom_layout.addWidget(self.meta_table)
        
        # Logs/Results
        self.log_label = QLabel("Ready. Load Image A and Image B to begin.")
        self.log_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.log_label.setWordWrap(True)
        bottom_layout.addWidget(self.log_label)
        
        content_splitter.addWidget(self.bottom_panel)
        content_splitter.setSizes([600, 200])
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_splitter)
        
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
        
        # Initial UI State
        self.update_ui_state()

    def create_button(self, text):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                border: none;
                padding: 10px;
                text-align: left;
                color: white;
                border-radius: 3px;
                margin: 2px 0;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #2c3e50;
                color: #7f8c8d;
            }
        """)
        return btn

    def log(self, message):
        self.log_label.setText(message)
        print(message)

    def update_ui_state(self):
        has_both = self.state.has_both_images()
        self.btn_analyze.setEnabled(has_both)
        self.btn_toggle_change.setEnabled(self.state.change_mask is not None)
        self.btn_export.setEnabled(self.state.change_results is not None)

    def update_metadata(self, data, slot):
        """Update metadata table with image info."""
        self.meta_table.setRowCount(0)
        if not data:
            return
            
        items = [
            (f"Image {slot}", os.path.basename(data.get('path', ''))),
            ("Size", f"{data['width']} x {data['height']}"),
            ("Bands", str(data['count'])),
            ("CRS", str(data['crs']))
        ]
        
        self.meta_table.setRowCount(len(items))
        for i, (key, value) in enumerate(items):
            self.meta_table.setItem(i, 0, QTableWidgetItem(key))
            self.meta_table.setItem(i, 1, QTableWidgetItem(value))

    def load_image(self, slot):
        path = open_file_dialog(self, f"Open Image {slot}")
        if path:
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
        
        self.update_ui_state()
    
    def on_raster_error(self, error, slot):
        """Callback when raster loading fails."""
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

    def run_analysis(self):
        if not self.state.has_both_images():
            return
        
        analysis_type = self.state.selected_analysis_type
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
        # TODO: Implement opacity adjustment on map layers
        # For now, just log the change
        print(f"Opacity changed to: {value}")
    
    def on_brightness_changed(self, value):
        """Handle brightness adjustment from symbology panel."""
        # TODO: Implement brightness adjustment
        print(f"Brightness changed to: {value}")
    
    def on_contrast_changed(self, value):
        """Handle contrast adjustment from symbology panel."""
        # TODO: Implement contrast adjustment
        print(f"Contrast changed to: {value}")
