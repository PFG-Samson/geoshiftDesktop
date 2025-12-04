import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui.main_window import MainWindow

def main():
    # Windows-specific: Set AppUserModelID to ensure taskbar icon updates
    try:
        import ctypes
        myappid = 'pfg.geoshift.desktop.1.0'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass  # Not on Windows or failed
    
    # Ensure High DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set application icon for taskbar (use .ico for better Windows compatibility)
    icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'logo.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
