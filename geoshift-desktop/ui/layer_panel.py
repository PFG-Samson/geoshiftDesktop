import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt

class LayerPanel(QWidget):
    """Panel that lists map layers with visibility toggles and removal actions.
    Emits signals that MainWindow can connect to MapWidget methods.
    """
    visibility_changed = pyqtSignal(str, bool)  # layer name, visible
    layer_removed = pyqtSignal(str)            # layer name
    layer_selected = pyqtSignal(str)           # layer name (e.g., for zoom)

    def __init__(self, map_widget, parent=None):
        super().__init__(parent)
        self.map_widget = map_widget
        self.setFixedWidth(200)
        self.setStyleSheet("background-color: #f9fafb; border-left: 1px solid #dcdde1;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.list = QListWidget()
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self.clear_all)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

    def refresh(self):
        """Refresh the list from the current layers in the map widget."""
        self.list.blockSignals(True)
        self.list.clear()
        for name, info in self.map_widget.layers.items():
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setCheckState(Qt.Checked if info.get('visible', True) else Qt.Unchecked)
            self.list.addItem(item)
        self.list.blockSignals(False)

    def _on_item_changed(self, item):
        name = item.text()
        visible = item.checkState() == Qt.Checked
        self.visibility_changed.emit(name, visible)

    def _on_item_double_clicked(self, item):
        name = item.text()
        self.layer_selected.emit(name)
        # Zoom to the selected layer using the map widget's method
        self.map_widget.zoom_to_layer(name)

    def clear_all(self):
        self.map_widget.clear_all_layers()
        self.refresh()

    def remove_selected(self):
        selected = self.list.currentItem()
        if selected:
            name = selected.text()
            self.map_widget.remove_layer(name)
            self.refresh()

