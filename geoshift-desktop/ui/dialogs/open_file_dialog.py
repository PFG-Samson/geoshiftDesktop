from PyQt5.QtWidgets import QFileDialog

def open_file_dialog(parent, title="Open Raster"):
    options = QFileDialog.Options()
    file_path, _ = QFileDialog.getOpenFileName(
        parent, 
        title, 
        "", 
        "Raster Files (*.tif *.tiff *.jpg *.jpeg *.png);;All Files (*)", 
        options=options
    )
    return file_path
