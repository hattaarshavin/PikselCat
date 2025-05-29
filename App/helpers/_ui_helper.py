from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from pathlib import Path

class UIHelper:
    @staticmethod
    def load_ui_file(ui_file_path, parent=None):
        """Load UI file and return the loaded widget"""
        ui_file = QFile(str(ui_file_path))
        
        if ui_file.open(QFile.ReadOnly):
            loader = QUiLoader()
            widget = loader.load(ui_file, parent)
            ui_file.close()
            return widget
        else:
            return None
    @staticmethod
    def get_ui_path(base_dir, ui_filename):
        """Get full path to UI file"""
        return base_dir / "App" / "gui" / "windows" / ui_filename
    
    @staticmethod
    def get_widget_ui_path(base_dir, ui_filename):
        """Get full path to widget UI file"""
        return base_dir / "App" / "gui" / "widgets" / ui_filename
