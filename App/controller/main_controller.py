from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer
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
        
        # Use UI helper to load main UI asynchronously
        self.ui_helper.load_main_ui_async(
            self.BASE_DIR, 
            "main_window.ui",
            self.on_ui_loaded,
            self.on_ui_error
        )
        
    def on_ui_loaded(self, ui_window):
        """Handle UI loaded event - runs in main thread"""
        if ui_window:
            # Copy the centralwidget from loaded UI to our window
            centralwidget = ui_window.centralWidget()
            if centralwidget:
                self.setCentralWidget(centralwidget)
                
                # Load widgets after UI is set
                QTimer.singleShot(0, self.load_widgets)
            
            # Copy menubar and statusbar if they exist
            if ui_window.menuBar():
                self.setMenuBar(ui_window.menuBar())
            if ui_window.statusBar():
                self.setStatusBar(ui_window.statusBar())
            
            # Set window properties
            self.setWindowTitle(self.config_manager.get("app_name"))
            self.resize(800, 600)
            self.center_on_screen()
            
            # Add the program icon
            icon_path = self.config_manager.get_icon_path()
            if icon_path.exists():
                window_icon = QIcon(str(icon_path))
                self.setWindowIcon(window_icon)
        
        # Load styles after UI is ready
        QTimer.singleShot(0, self.load_styles)
        
    def on_ui_error(self, error_message):
        """Handle UI loading error"""
        from PySide6.QtWidgets import QLabel
        fallback_label = QLabel(f"UI Loading Error: {error_message}")
        fallback_label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(fallback_label)
        
    def load_styles(self):
        """Load CSS styles from main_style.css"""
        try:
            css_content = self.ui_helper.load_css_file(self.BASE_DIR, "main_style.css")
            if css_content:
                self.setStyleSheet(css_content)
        except Exception as e:
            print(f"Error loading styles: {e}")
    
    def load_widgets(self):
        """Load and integrate the widget UIs using UI helper"""
        from PySide6.QtWidgets import QWidget
        
        try:
            # Find the container widgets
            central_widget = self.centralWidget()
            if not central_widget:
                return
                
            actions_container = central_widget.findChild(QWidget, "actionsContainer")
            statistics_container = central_widget.findChild(QWidget, "statisticsContainer")
            workspace_container = central_widget.findChild(QWidget, "workspaceContainer")
            
            # Load actions widget using UI helper
            if actions_container:
                actions_widget = self.ui_helper.load_widget_safely(
                    self.BASE_DIR, "actions.ui", actions_container
                )
                if actions_widget:
                    from App.controller.actions import ActionsController
                    self.actions_controller = ActionsController(actions_widget)
            
            # Load statistics widget using UI helper
            if statistics_container:
                self.ui_helper.load_widget_safely(
                    self.BASE_DIR, "statistics.ui", statistics_container
                )
            
            # Load workspace widget using UI helper
            if workspace_container:
                workspace_widget = self.ui_helper.load_widget_safely(
                    self.BASE_DIR, "workspace.ui", workspace_container
                )
                if workspace_widget:
                    # Load DnD area inside workspace using UI helper
                    dnd_container = workspace_widget.findChild(QWidget, "dndContainer")
                    if dnd_container:
                        self.ui_helper.load_dnd_widget_safely(
                            self.BASE_DIR, 
                            dnd_container, 
                            workspace_widget,
                            self.init_dnd_handler
                        )
                
        except Exception as e:
            print(f"Error loading widgets: {e}")
    def init_dnd_handler(self, dnd_widget, workspace_widget, work_area_widget):
        """Initialize DnD handler safely"""
        try:
            from App.controller.dnd_handler import DndHandler
            from PySide6.QtWidgets import QPushButton
            
            # Find the buttons in the DnD widget
            open_files_btn = dnd_widget.findChild(QPushButton, "openFilesButton")
            open_folder_btn = dnd_widget.findChild(QPushButton, "openFolderButton")
            
            if open_files_btn and open_folder_btn:
                self.dnd_handler = DndHandler(
                    dnd_widget, 
                    workspace_widget, 
                    work_area_widget,
                    open_files_btn, 
                    open_folder_btn
                )
            else:
                print("Error: Could not find DnD buttons")
        except Exception as e:
            print(f"Error initializing DnD handler: {e}")
    
    def center_on_screen(self):
        """Center the window on screen"""
        screen = QApplication.primaryScreen().availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
