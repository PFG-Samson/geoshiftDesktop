import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QSplitter, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QFileDialog, QScrollArea
)
from PyQt5.QtCore import Qt
from ui.map_widget import MapWidget
from ui.dialogs.open_file_dialog import open_file_dialog
from core.reader import load_raster
from core.analysis_water import compute_ndwi, threshold_water, predict_water_cnn
from core.mask_tools import calculate_area
from core.exporter import export_report
from app import AppState
import numpy as np
from PIL import Image

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Geoshift Desktop (MVP)")
        self.resize(1200, 800)
        
        self.state = AppState()
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("background-color: #2c3e50; color: white;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        # Branding
        title_label = QLabel("GEOSHIFT")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title_label)
        
        # Buttons
        self.btn_open = self.create_button("Open Image (Single)")
        self.btn_load_a = self.create_button("Load Image A")
        self.btn_load_b = self.create_button("Load Image B")
        self.btn_compare = self.create_button("Activate Compare Mode")
        self.btn_compare.setCheckable(True)
        
        self.add_separator(sidebar_layout)
        
        self.btn_analyze = self.create_button("Run Water Analysis")
        self.btn_toggle_mask = self.create_button("Toggle Mask Overlay")
        self.btn_export = self.create_button("Export Report")
        
        sidebar_layout.addWidget(self.btn_open)
        sidebar_layout.addWidget(self.btn_load_a)
        sidebar_layout.addWidget(self.btn_load_b)
        sidebar_layout.addWidget(self.btn_compare)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #34495e; margin: 10px 0;")
        sidebar_layout.addWidget(line)
        
        sidebar_layout.addWidget(self.btn_analyze)
        sidebar_layout.addWidget(self.btn_toggle_mask)
        sidebar_layout.addWidget(self.btn_export)
        
        sidebar_layout.addStretch()
        
        # Main Content Area (Map + Bottom Panel)
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
        self.log_label = QLabel("Ready.")
        self.log_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.log_label.setWordWrap(True)
        bottom_layout.addWidget(self.log_label)
        
        content_splitter.addWidget(self.bottom_panel)
        content_splitter.setSizes([600, 200])
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_splitter)
        
        # Connect Signals
        self.btn_open.clicked.connect(self.open_single_image)
        self.btn_load_a.clicked.connect(lambda: self.load_comparison_image('A'))
        self.btn_load_b.clicked.connect(lambda: self.load_comparison_image('B'))
        self.btn_compare.clicked.connect(self.toggle_compare_mode)
        self.btn_analyze.clicked.connect(self.run_analysis)
        self.btn_toggle_mask.clicked.connect(self.toggle_mask)
        self.btn_export.clicked.connect(self.export_report)
        
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
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:checked {
                background-color: #16a085;
            }
        """)
        return btn

    def add_separator(self, layout):
        pass # Already added manually

    def log(self, message):
        self.log_label.setText(message)
        print(message)

    def update_ui_state(self):
        is_compare = self.state.compare_mode
        self.btn_analyze.setEnabled(not is_compare and self.state.raster is not None)
        self.btn_toggle_mask.setEnabled(not is_compare and self.state.mask is not None)
        self.btn_export.setEnabled(not is_compare and self.state.results is not None)
        
        if is_compare:
            self.btn_compare.setText("Deactivate Compare Mode")
            self.btn_compare.setChecked(True)
        else:
            self.btn_compare.setText("Activate Compare Mode")
            self.btn_compare.setChecked(False)

    def update_metadata(self, data):
        self.meta_table.setRowCount(0)
        if not data:
            return
            
        items = [
            ("File", os.path.basename(data.get('path', ''))),
            ("Size", f"{data['width']} x {data['height']}"),
            ("Bands", str(data['count'])),
            ("CRS", str(data['crs'])),
            ("Bounds", str(data['bounds']))
        ]
        
        self.meta_table.setRowCount(len(items))
        for i, (key, value) in enumerate(items):
            self.meta_table.setItem(i, 0, QTableWidgetItem(key))
            self.meta_table.setItem(i, 1, QTableWidgetItem(value))

    def open_single_image(self):
        path = open_file_dialog(self)
        if path:
            self.log(f"Loading {path}...")
            data = load_raster(path)
            if data:
                self.state.reset_single_mode()
                self.state.raster = data
                self.state.raster_path = path
                self.state.compare_mode = False
                
                self.update_metadata(data)
                self.map_widget.show_map(data)
                self.log(f"Loaded {os.path.basename(path)}")
                self.update_ui_state()
            else:
                self.log("Failed to load raster.")

    def load_comparison_image(self, slot):
        path = open_file_dialog(self, f"Open Image {slot}")
        if path:
            self.log(f"Loading Image {slot}: {path}...")
            data = load_raster(path)
            if data:
                if slot == 'A':
                    self.state.raster_a = data
                else:
                    self.state.raster_b = data
                self.log(f"Loaded Image {slot}")
                
                # If compare mode is active, refresh map
                if self.state.compare_mode:
                    self.map_widget.show_comparison(self.state.raster_a, self.state.raster_b)
            else:
                self.log(f"Failed to load Image {slot}.")

    def toggle_compare_mode(self):
        if not self.state.compare_mode:
            # Activate
            if self.state.raster_a and self.state.raster_b:
                self.state.compare_mode = True
                self.map_widget.show_comparison(self.state.raster_a, self.state.raster_b)
                self.log("Compare Mode Activated")
            else:
                QMessageBox.warning(self, "Warning", "Please load both Image A and Image B first.")
                self.btn_compare.setChecked(False)
                return
        else:
            # Deactivate
            self.state.compare_mode = False
            # Restore single mode view if available
            if self.state.raster:
                self.map_widget.show_map(self.state.raster, 
                                         "mask.png" if self.state.mask is not None and self.state.mask_visible else None)
            else:
                self.map_widget.show_map(None)
            self.log("Compare Mode Deactivated")
            
        self.update_ui_state()

    def run_analysis(self):
        if not self.state.raster:
            return
            
        self.log("Running Water Analysis...")
        
        # Check bands
        count = self.state.raster['count']
        array = self.state.raster['array']
        
        mask = None
        
        # Simple heuristic: If > 3 bands, assume multispectral. 
        # Usually Green is 3 (or 2 depending on RGB/BGR) and NIR is 8 or 4.
        # For MVP, let's assume:
        # 4 bands: R, G, B, NIR (common in drones/satellites) -> Green=1, NIR=3 (0-indexed)
        # Or just try to use indices provided by user? No UI for that yet.
        # Let's fallback to CNN if < 4 bands.
        
        if count >= 4:
            try:
                # Assuming Band 2 is Green, Band 4 is NIR (Sentinel-2 style: B3=Green, B8=NIR)
                # But rasterio reads sequentially.
                # Let's try: Green=1, NIR=3 (0-indexed)
                green = array[1]
                nir = array[3]
                ndwi = compute_ndwi(green, nir)
                mask = threshold_water(ndwi)
                self.state.ndwi = ndwi
                self.log("NDWI Analysis Complete.")
            except Exception as e:
                self.log(f"NDWI Error: {e}. Falling back to CNN.")
        
        if mask is None:
            # Fallback to CNN or simple threshold on Blue?
            # Let's try CNN placeholder
            mask = predict_water_cnn(array)
            if mask is None:
                # Mock mask for MVP demonstration if everything fails
                # Create a dummy mask based on simple brightness threshold on first band
                self.log("Using brightness threshold fallback.")
                mask = (array[0] < 50).astype(np.uint8) # Dark pixels = water?
        
        if mask is not None:
            self.state.mask = mask
            
            # Calculate Area
            results = calculate_area(mask, self.state.raster['transform'])
            self.state.results = results
            
            # Save mask to file for Folium overlay
            mask_img = Image.fromarray(mask * 255, mode='L')
            # Make transparent: 0 is transparent, 1 is blue
            # Create RGBA
            mask_rgba = Image.new("RGBA", mask_img.size, (0, 0, 255, 0))
            # Paste blue where mask is 1
            # Actually, let's just make a blue image and use mask as alpha
            blue = Image.new("RGBA", mask_img.size, (0, 0, 255, 150)) # Semi-transparent blue
            # We need an alpha mask where 1->255, 0->0
            alpha = mask_img.point(lambda x: 150 if x > 0 else 0)
            blue.putalpha(alpha)
            
            mask_path = "mask.png"
            blue.save(mask_path)
            
            self.map_widget.show_map(self.state.raster, mask_path)
            
            # Update logs
            self.log(f"Analysis Done. Water Area: {results['area_ha']:.2f} ha ({results['percent_coverage']:.2f}%)")
            self.update_ui_state()
        else:
            self.log("Analysis failed to generate a mask.")

    def toggle_mask(self):
        if self.state.mask is not None:
            self.state.mask_visible = not self.state.mask_visible
            mask_path = "mask.png" if self.state.mask_visible else None
            self.map_widget.show_map(self.state.raster, mask_path)

    def export_report(self):
        if self.state.results:
            path, _ = QFileDialog.getSaveFileName(self, "Save Report", "report.html", "HTML Files (*.html)")
            if path:
                data = {
                    **self.state.results,
                    **self.state.raster,
                    "preview_path": self.state.raster['preview_path']
                }
                success = export_report(data, path)
                if success:
                    QMessageBox.information(self, "Success", "Report exported successfully.")
                else:
                    QMessageBox.critical(self, "Error", "Failed to export report.")
