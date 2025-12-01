from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal

class SymbologyPanel(QWidget):
    """Panel for adjusting image visualization parameters."""
    
    # Signals emitted when parameters change
    opacity_changed = pyqtSignal(float)  # 0.0 to 1.0
    brightness_changed = pyqtSignal(float)  # -1.0 to 1.0
    contrast_changed = pyqtSignal(float)  # 0.0 to 2.0
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Group box
        group = QGroupBox("Image Symbology")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #34495e;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        group_layout = QVBoxLayout()
        
        # Opacity slider
        opacity_label = QLabel("Opacity: 100%")
        opacity_label.setStyleSheet(" color: #2c3e50;")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setStyleSheet(self._slider_style())
        self.opacity_slider.valueChanged.connect(
            lambda v: self._on_opacity_changed(v, opacity_label)
        )
        
        group_layout.addWidget(opacity_label)
        group_layout.addWidget(self.opacity_slider)
        
        # Brightness slider
        brightness_label = QLabel("Brightness: 0%")
        brightness_label.setStyleSheet(" color: #2c3e50;")
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setMinimum(-100)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.setStyleSheet(self._slider_style())
        self.brightness_slider.valueChanged.connect(
            lambda v: self._on_brightness_changed(v, brightness_label)
        )
        
        group_layout.addWidget(brightness_label)
        group_layout.addWidget(self.brightness_slider)
        
        # Contrast slider
        contrast_label = QLabel("Contrast: 100%")
        contrast_label.setStyleSheet(" color: #2c3e50;")
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setMinimum(0)
        self.contrast_slider.setMaximum(200)
        self.contrast_slider.setValue(100)
        self.contrast_slider.setStyleSheet(self._slider_style())
        self.contrast_slider.valueChanged.connect(
            lambda v: self._on_contrast_changed(v, contrast_label)
        )
        
        group_layout.addWidget(contrast_label)
        group_layout.addWidget(self.contrast_slider)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()
    
    def _slider_style(self):
        return """
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #34495e;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #2980b9;
                border: 1px solid #2980b9;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #3498db;
            }
        """
    
    def _on_opacity_changed(self, value, label):
        label.setText(f"Opacity: {value}%")
        self.opacity_changed.emit(value / 100.0)
    
    def _on_brightness_changed(self, value, label):
        label.setText(f"Brightness: {value:+d}%")
        self.brightness_changed.emit(value / 100.0)
    
    def _on_contrast_changed(self, value, label):
        label.setText(f"Contrast: {value}%")
        self.contrast_changed.emit(value / 100.0)
    
    def reset(self):
        """Reset all sliders to default values."""
        self.opacity_slider.setValue(100)
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(100)
