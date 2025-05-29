from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QIcon
from pathlib import Path
import os

class MainController(QMainWindow):
    def __init__(self, base_dir):
        super().__init__()
        self.BASE_DIR = base_dir
        
        # Import dependencies
        from App.config.config_manager import ConfigManager
        from App.helpers._ui_helper import UIHelper
        
        self.config_manager = ConfigManager(base_dir)
        self.ui_helper = UIHelper()
        
        self.load_ui()
        
    def load_ui(self):
        """Load the main window UI"""
        ui_file_path = self.ui_helper.get_ui_path(self.BASE_DIR, "main_window.ui")
        self.window = self.ui_helper.load_ui_file(ui_file_path, self)
        
        if self.window:
            # Set window properties
            self.setWindowTitle(self.config_manager.get("app_name"))
            
            # Add the program icon
            icon_path = self.config_manager.get_icon_path()
            if icon_path.exists():
                window_icon = QIcon(str(icon_path))
                self.setWindowIcon(window_icon)
            else:
                print(f"Icon not found: {icon_path}")
