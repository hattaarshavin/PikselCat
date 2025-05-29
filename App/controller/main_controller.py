from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
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
        self.load_styles()
        
    def load_styles(self):
        """Load CSS styles from main_style.css"""
        css_content = self.ui_helper.load_css_file(self.BASE_DIR, "main_style.css")
        if css_content:
            self.setStyleSheet(css_content)
        
    def load_ui(self):
        """Load the main window UI"""
        ui_file_path = self.ui_helper.get_ui_path(self.BASE_DIR, "main_window.ui")
        ui_window = self.ui_helper.load_ui_file(ui_file_path, None)
        
        if ui_window:
            # Copy the centralwidget from loaded UI to our window
            centralwidget = ui_window.centralWidget()
            if centralwidget:
                self.setCentralWidget(centralwidget)
                
                # Load and add the widget UIs
                self.load_widgets()
            
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
        else:
            # Fallback if UI loading fails
            from PySide6.QtWidgets import QLabel
            fallback_label = QLabel("Hello World from PikselCat!")
            fallback_label.setAlignment(Qt.AlignCenter)
            self.setCentralWidget(fallback_label)
    
    def load_widgets(self):
        """Load and integrate the widget UIs"""
        from PySide6.QtWidgets import QVBoxLayout, QWidget
        
        # Find the container widgets
        central_widget = self.centralWidget()
        actions_container = central_widget.findChild(QWidget, "actionsContainer")
        statistics_container = central_widget.findChild(QWidget, "statisticsContainer")
        workspace_container = central_widget.findChild(QWidget, "workspaceContainer")
        
        # Load actions widget
        if actions_container:
            actions_ui_path = self.ui_helper.get_widget_ui_path(self.BASE_DIR, "actions.ui")
            actions_widget = self.ui_helper.load_ui_file(actions_ui_path, actions_container)
            if actions_widget:
                layout = QVBoxLayout(actions_container)
                layout.addWidget(actions_widget)
                actions_container.setLayout(layout)
                
                # Initialize actions controller
                from App.controller.actions import ActionsController
                self.actions_controller = ActionsController(actions_widget)
        
        # Load statistics widget
        if statistics_container:
            statistics_ui_path = self.ui_helper.get_widget_ui_path(self.BASE_DIR, "statistics.ui")
            statistics_widget = self.ui_helper.load_ui_file(statistics_ui_path, statistics_container)
            if statistics_widget:
                layout = QVBoxLayout(statistics_container)
                layout.addWidget(statistics_widget)
                statistics_container.setLayout(layout)
        
        # Load workspace widget with DnD area
        if workspace_container:
            workspace_ui_path = self.ui_helper.get_widget_ui_path(self.BASE_DIR, "workspace.ui")
            workspace_widget = self.ui_helper.load_ui_file(workspace_ui_path, workspace_container)
            if workspace_widget:
                layout = QVBoxLayout(workspace_container)
                layout.addWidget(workspace_widget)
                workspace_container.setLayout(layout)
                
                # Load DnD area inside workspace
                dnd_container = workspace_widget.findChild(QWidget, "dndContainer")
                if dnd_container:
                    dnd_ui_path = self.ui_helper.get_widget_ui_path(self.BASE_DIR, "dnd_area.ui")
                    dnd_widget = self.ui_helper.load_ui_file(dnd_ui_path, dnd_container)
                    if dnd_widget:
                        dnd_layout = QVBoxLayout(dnd_container)
                        dnd_layout.addWidget(dnd_widget)
                        dnd_container.setLayout(dnd_layout)
                        
                        # Initialize DnD handler
                        from App.controller.dnd_handler import DndHandler
                        self.dnd_handler = DndHandler(
                            dnd_widget, 
                            workspace_widget,
                            dnd_widget.openFilesButton,
                            dnd_widget.openFolderButton
                        )
    
    def center_on_screen(self):
        """Center the window on screen"""
        screen = QApplication.primaryScreen().availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
