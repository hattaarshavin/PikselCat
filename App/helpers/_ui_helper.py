from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget
from pathlib import Path

class UIHelper:
    def __init__(self):
        pass
    
    def load_main_ui_async(self, base_dir, ui_filename, success_callback, error_callback):
        """Load main UI asynchronously using QTimer to defer execution"""
        def load_ui():
            try:
                ui_file_path = self.get_ui_path(base_dir, ui_filename)
                ui_window = self.load_ui_file(ui_file_path, None)
                if ui_window:
                    success_callback(ui_window)
                else:
                    error_callback("Failed to load UI file")
            except Exception as e:
                error_callback(str(e))
        
        # Use QTimer to defer UI loading to next event loop cycle
        QTimer.singleShot(0, load_ui)      
    def load_widget_safely(self, base_dir, ui_filename, container_widget):
        """Load widget UI safely with error handling"""
        try:
            widget_ui_path = self.get_widget_ui_path(base_dir, ui_filename)
            widget = self.load_ui_file(widget_ui_path, None)  # Don't set parent during loading
            if widget and container_widget:
                layout = QVBoxLayout(container_widget)
                layout.setContentsMargins(0, 0, 0, 0)  # No margin for full width
                layout.setSpacing(0)  # Remove spacing
                layout.addWidget(widget)  # Set parent here in main thread
                container_widget.setLayout(layout)
                return widget
        except Exception as e:
            print(f"Error loading widget {ui_filename}: {e}")
        return None
    def load_dnd_widget_safely(self, base_dir, dnd_container, workspace_widget, init_callback):
        """Load DnD widget safely with initialization callback"""
        try:
            # Load DnD widget
            dnd_ui_path = self.get_widget_ui_path(base_dir, "dnd_area.ui")
            dnd_widget = self.load_ui_file(dnd_ui_path, None)
            
            # Load Work Area widget
            work_area_ui_path = self.get_widget_ui_path(base_dir, "work_area.ui")
            work_area_widget = self.load_ui_file(work_area_ui_path, None)
            
            if dnd_widget and work_area_widget:                # Setup DnD container
                dnd_layout = QVBoxLayout(dnd_container)
                dnd_layout.setContentsMargins(0, 0, 0, 0)  # No margin for full width
                dnd_layout.setSpacing(0)  # Remove spacing
                dnd_layout.addWidget(dnd_widget)
                dnd_container.setLayout(dnd_layout)                # Setup Work Area container
                work_area_container = workspace_widget.findChild(QWidget, "workAreaContainer")
                if work_area_container:
                    work_area_layout = QVBoxLayout(work_area_container)
                    work_area_layout.setContentsMargins(0, 0, 0, 0)  # No margin for full width
                    work_area_layout.setSpacing(0)  # Remove spacing
                    work_area_layout.addWidget(work_area_widget)
                    work_area_container.setLayout(work_area_layout)
                
                # Initialize DnD handler in main thread
                QTimer.singleShot(0, lambda: init_callback(dnd_widget, workspace_widget, work_area_widget))
                return dnd_widget
        except Exception as e:
            print(f"Error loading DnD widget: {e}")
        return None
    
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
    
    @staticmethod
    def load_css_file(base_dir, css_filename):
        """Load CSS file and return the content as string"""
        css_file_path = base_dir / "App" / "gui" / "windows" / css_filename
        if css_file_path.exists():
            with open(css_file_path, 'r', encoding='utf-8') as file:
                return file.read()
        return ""
