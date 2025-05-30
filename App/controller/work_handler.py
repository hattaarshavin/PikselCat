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
        """Load files into work area with two-stage loading process"""
        self.loaded_files = files
        
        # Stage 1 is already complete (file validation), now do Stage 2 (widget creation)
        self.start_widget_creation()
    def start_widget_creation(self):
        """Start the widget creation process with progress tracking"""
        if not self.loaded_files:
            self.switch_to_work_area()
            return
            
        # Check if we already have a progress dialog from the validation stage
        if not hasattr(self, 'progress_dialog') or not self.progress_dialog:
            # Create progress dialog for widget creation stage
            from App.gui.dialogs.progress_dialog import ProgressDialog
            
            self.progress_dialog = ProgressDialog(self.work_area_widget)
            self.progress_dialog.set_stage("widgets", 0)
            self.progress_dialog.cancel_requested.connect(self.cancel_widget_creation)
            self.progress_dialog.show()
        else:
            # Progress dialog exists from validation stage - just update it
            self.progress_dialog.set_stage("widgets", 0)
            # Connect cancel signal if not already connected
            try:
                self.progress_dialog.cancel_requested.connect(self.cancel_widget_creation)
            except:
                pass  # Already connected
        
        # Clear existing file widgets first
        scroll_area = self.work_area_widget.findChild(QWidget, "scrollAreaWidgetContents")
        if scroll_area:
            file_list_layout = scroll_area.findChild(QVBoxLayout, "fileListLayout")
            if file_list_layout:
                self.clear_file_widgets(file_list_layout)
        
        # Create widget creation manager
        from App.helpers.widget_loader_worker import WidgetCreationManager
        
        self.widget_manager = WidgetCreationManager(self)
        self.widget_manager.progress_updated.connect(self.on_widget_progress_updated)
        self.widget_manager.widget_created.connect(self.on_widget_created)
        self.widget_manager.loading_completed.connect(self.on_widget_creation_completed)
        self.widget_manager.loading_cancelled.connect(self.on_widget_creation_cancelled)
        
        # Start widget creation
        self.widget_manager.start_creation(self.loaded_files, scroll_area)
        
        # Switch to work area immediately
        self.switch_to_work_area()
    
    def on_widget_progress_updated(self, progress, status):
        """Handle progress updates from widget creation"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.set_value(progress)
            self.progress_dialog.set_status(status)
    
    def on_widget_created(self, widget):
        """Handle individual widget creation"""
        # Add widget to layout
        scroll_area = self.work_area_widget.findChild(QWidget, "scrollAreaWidgetContents")
        if scroll_area:
            file_list_layout = scroll_area.findChild(QVBoxLayout, "fileListLayout")
            if file_list_layout:
                # Remove any existing stretch before adding widget
                if file_list_layout.count() > 0:
                    last_item = file_list_layout.itemAt(file_list_layout.count() - 1)
                    if last_item and last_item.spacerItem():
                        file_list_layout.removeItem(last_item)
                
                self.file_widgets.append(widget)
                file_list_layout.addWidget(widget)
    
    def on_widget_creation_completed(self, widgets):
        """Handle completion of widget creation"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Add final stretch to push widgets to the top
        scroll_area = self.work_area_widget.findChild(QWidget, "scrollAreaWidgetContents")
        if scroll_area:
            file_list_layout = scroll_area.findChild(QVBoxLayout, "fileListLayout")
            if file_list_layout:
                file_list_layout.addStretch()
        
        # Update header with final counts
        self.update_work_area_header()
        
        self.status_helper.show_success(f"Created {len(widgets)} file widgets")
        
        # Clean up widget manager
        if hasattr(self, 'widget_manager'):
            self.widget_manager.deleteLater()
            self.widget_manager = None
    
    def on_widget_creation_cancelled(self):
        """Handle cancellation of widget creation"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.status_helper.show_status("Widget creation cancelled", self.status_helper.PRIORITY_NORMAL)
        
        # Clean up widget manager
        if hasattr(self, 'widget_manager'):
            self.widget_manager.deleteLater()
            self.widget_manager = None
    def cancel_widget_creation(self):
        """Cancel the widget creation operation"""
        if hasattr(self, 'widget_manager') and self.widget_manager:
            self.widget_manager.cancel()
    
    def clear_files(self):
        """Clear all loaded files and switch back to DnD area"""
        # Cancel any ongoing widget creation
        if hasattr(self, 'widget_manager') and self.widget_manager:
            self.widget_manager.cancel()
        
        # Close any open progress dialog
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Clear file data and widgets
        self.loaded_files = []
        
        # Clear the UI
        scroll_area = self.work_area_widget.findChild(QWidget, "scrollAreaWidgetContents")
        if scroll_area:
            file_list_layout = scroll_area.findChild(QVBoxLayout, "fileListLayout")
            if file_list_layout:
                self.clear_file_widgets(file_list_layout)
        
        self.switch_to_dnd_area()
        self.files_cleared.emit()
        
        self.status_helper.show_ready("Ready for new files")
    def switch_to_work_area(self):
        """Switch to work area view"""
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(1)  # Work area is at index 1
    
    def switch_to_dnd_area(self):
        """Switch to DnD area view"""
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)  # DnD area is at index 0
    
    def update_work_area_header(self):
        """Update the work area header with file and folder counts"""
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
        else:
            # No files loaded
            if title_label:
                title_label.setText("Work Area")
    def clear_file_widgets(self, layout):
        """Clear all existing file widgets from the layout"""
        # Remove widgets from layout and delete them
        while layout.count():
            child = layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
            # Handle spacers and other layout items
            elif child.spacerItem():
                # Spacer items don't need special cleanup
                pass
        
        # Clear our widget references
        self.file_widgets.clear()
    
    def get_loaded_files(self):
        """Get the currently loaded files"""
        return self.loaded_files
    
    def get_loaded_files_count(self):
        """Get the count of loaded files"""
        return len(self.loaded_files)