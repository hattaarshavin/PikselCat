from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import QObject, Signal, Qt
import qtawesome as qta
import os
from .loaded_item_widget import LoadedItemWidget

class WorkHandler(QObject):
    """Handler for work area operations and file processing"""
    # Signals for communication with other components
    files_cleared = Signal()
    
    def __init__(self, workspace_widget: QWidget, work_area_widget: QWidget, status_helper):
        super().__init__()
        self.workspace_widget = workspace_widget
        self.work_area_widget = work_area_widget
        self.status_helper = status_helper
        self.loaded_files = []
        self.file_widgets = []  # Store references to LoadedItemWidget instances
        
        # Get the stacked widget for switching between DnD and Work Area
        self.stacked_widget = workspace_widget.findChild(QStackedWidget, "stackedWidget")
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the work area UI elements with icons"""
        if self.work_area_widget:
            # Find and set icon for clear button (using X icon instead of trash)
            clear_btn = self.work_area_widget.findChild(QPushButton, "clearFilesButton")
            if clear_btn:                
                clear_icon = qta.icon('fa6s.xmark', color='white')
                clear_btn.setIcon(clear_icon)
    
    def setup_connections(self):
        """Setup work area button connections"""
        if self.work_area_widget:
            clear_btn = self.work_area_widget.findChild(QPushButton, "clearFilesButton")
            if clear_btn:
                clear_btn.clicked.connect(self.clear_files)
    
    def load_files(self, files):
        """Load files into work area"""
        self.loaded_files = files
        self.update_work_area_display()
        self.switch_to_work_area()
        
        self.status_helper.show_success("File loading", len(files))
    
    def clear_files(self):
        """Clear all loaded files and switch back to DnD area"""
        self.loaded_files = []
        self.file_widgets = []
        self.switch_to_dnd_area()
        self.files_cleared.emit()
        
        self.status_helper.show_ready("Ready for new files")
    
    def switch_to_work_area(self):
        """Switch to work area view"""
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(1)  # Work area is at index 1
            self.update_work_area_display()
    
    def switch_to_dnd_area(self):
        """Switch to DnD area view"""
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)  # DnD area is at index 0
    
    def update_work_area_display(self):
        """Update the work area with loaded files using individual widgets"""
        if not self.work_area_widget:
            return
            
        # Get the file list layout from the scroll area
        scroll_area = self.work_area_widget.findChild(QWidget, "scrollAreaWidgetContents")
        if not scroll_area:
            return
            
        file_list_layout = scroll_area.findChild(QVBoxLayout, "fileListLayout")
        if not file_list_layout:
            return
        
        # Clear existing file widgets
        self.clear_file_widgets(file_list_layout)
        
        # Update header title with file count and folder count
        title_label = self.work_area_widget.findChild(QLabel, "workAreaTitle")
        
        if self.loaded_files:
            # Count unique folders
            folders = set()
            for file_path in self.loaded_files:
                folder_path = os.path.dirname(file_path)
                if folder_path:
                    folders.add(folder_path)
            
            file_count = len(self.loaded_files)
            folder_count = len(folders)
            
            # Update title with counts
            if title_label:
                title_text = f"{file_count} files loaded ({folder_count} folder{'s' if folder_count != 1 else ''})"
                title_label.setText(title_text)
              # Create individual widgets for each file
            from ..helpers._ui_helper import UIHelper
            ui_helper = UIHelper()
            for file_path in self.loaded_files:
                file_widget = LoadedItemWidget(file_path, ui_helper, scroll_area)
                file_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                self.file_widgets.append(file_widget)
                file_list_layout.addWidget(file_widget)
            
            # Add a stretch to push widgets to the top
            file_list_layout.addStretch()
            
        else:
            # No files loaded - add empty state label
            if title_label:
                title_label.setText("Work Area")
            
            empty_label = QLabel("No files loaded")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
            file_list_layout.addWidget(empty_label)
            file_list_layout.addStretch()
    
    def clear_file_widgets(self, layout):
        """Clear all existing file widgets from the layout"""
        # Remove widgets from layout and delete them
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
                child.widget().deleteLater()
        
        # Clear our widget references
        self.file_widgets.clear()
    
    def get_loaded_files(self):
        """Get the currently loaded files"""
        return self.loaded_files
    
    def get_loaded_files_count(self):
        """Get the count of loaded files"""
        return len(self.loaded_files)