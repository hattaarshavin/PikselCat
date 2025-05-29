from PySide6.QtWidgets import QWidget, QLabel, QFileDialog, QPushButton, QStackedWidget
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent, QDragLeaveEvent
import os

class DragDropWidget(QWidget):
    """Custom widget that handles drag and drop events properly"""
    files_dropped = Signal(list)
    drag_entered = Signal()
    drag_left = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        # Make widget transparent to mouse events except drag/drop
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drag_entered.emit()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.drag_left.emit()
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    files.append(file_path)
                elif os.path.isdir(file_path):
                    # If it's a directory, get all files in it
                    for root, dirs, filenames in os.walk(file_path):
                        for filename in filenames:
                            files.append(os.path.join(root, filename))
            
            if files:
                self.files_dropped.emit(files)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
        
        self.drag_left.emit()

class DndHandler(QObject):
    # Signal emitted when files are loaded
    files_loaded = Signal(list)
    
    def __init__(self, dnd_widget: QWidget, workspace_widget: QWidget, work_area_widget: QWidget, open_files_btn: QPushButton, open_folder_btn: QPushButton):
        super().__init__()
        self.dnd_widget = dnd_widget
        self.workspace_widget = workspace_widget
        self.work_area_widget = work_area_widget
        self.loaded_files = []
        self.last_directory = ""  # Track last used directory
        
        # Get the stacked widget for switching between DnD and Work Area
        self.stacked_widget = workspace_widget.findChild(QStackedWidget, "stackedWidget")
        self.setup_connections(open_files_btn, open_folder_btn)
        self.setup_work_area_connections()
        self.setup_drag_drop()
        
        # Initially show DnD area (index 0)
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)
    def setup_connections(self, open_files_btn: QPushButton, open_folder_btn: QPushButton):
        """Setup button connections"""
        open_files_btn.clicked.connect(self.open_files)
        open_folder_btn.clicked.connect(self.open_folder)
    
    def setup_work_area_connections(self):
        """Setup work area button connections"""
        if self.work_area_widget:
            clear_btn = self.work_area_widget.findChild(QPushButton, "clearFilesButton")
            process_btn = self.work_area_widget.findChild(QPushButton, "processFilesButton")
            
            if clear_btn:
                clear_btn.clicked.connect(self.clear_files)
            if process_btn:
                process_btn.clicked.connect(self.process_files)
    def setup_drag_drop(self):
        """Setup drag and drop functionality using proper widget overlay"""
        if self.dnd_widget:
            # Create a custom drag drop overlay that covers the entire widget
            from PySide6.QtWidgets import QVBoxLayout
            
            # Create overlay widget for drag and drop
            self.drag_drop_overlay = DragDropWidget(self.dnd_widget)
            self.drag_drop_overlay.setGeometry(self.dnd_widget.rect())
            self.drag_drop_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.drag_drop_overlay.show()
            
            # Connect signals
            self.drag_drop_overlay.files_dropped.connect(self.load_files)
            self.drag_drop_overlay.drag_entered.connect(self.on_drag_enter)
            self.drag_drop_overlay.drag_left.connect(self.on_drag_leave)
            
            # Ensure overlay resizes with parent
            def resize_overlay():
                if hasattr(self, 'drag_drop_overlay'):
                    self.drag_drop_overlay.setGeometry(self.dnd_widget.rect())
                    self.dnd_widget.resizeEvent = lambda event: (
                resize_overlay(),
                QWidget.resizeEvent(self.dnd_widget, event)
            )[1]
    def on_drag_enter(self):
        """Handle drag enter visual feedback"""
        if hasattr(self, 'drag_drop_overlay'):
            self.drag_drop_overlay.setProperty("dragHover", True)
            self.drag_drop_overlay.style().unpolish(self.drag_drop_overlay)
            self.drag_drop_overlay.style().polish(self.drag_drop_overlay)
        # Also apply to the main widget for visual feedback
        self.dnd_widget.setProperty("dragHover", True)
        self.dnd_widget.style().unpolish(self.dnd_widget)
        self.dnd_widget.style().polish(self.dnd_widget)
    
    def on_drag_leave(self):
        """Handle drag leave visual feedback"""
        if hasattr(self, 'drag_drop_overlay'):
            self.drag_drop_overlay.setProperty("dragHover", False)
            self.drag_drop_overlay.style().unpolish(self.drag_drop_overlay)
            self.drag_drop_overlay.style().polish(self.drag_drop_overlay)
        # Also remove from the main widget
        self.dnd_widget.setProperty("dragHover", False)
        self.dnd_widget.style().unpolish(self.dnd_widget)
        self.dnd_widget.style().polish(self.dnd_widget)

    def open_files(self):
        """Open file dialog to select multiple files"""
        files, _ = QFileDialog.getOpenFileNames(
            self.dnd_widget,
            "Select Files",
            self.last_directory,
            "All Files (*.*)"
        )
        if files:
            # Update last directory to the directory of the first selected file
            self.last_directory = os.path.dirname(files[0])
            self.load_files(files)
    
    def open_folder(self):
        """Open folder dialog to select a folder"""
        folder = QFileDialog.getExistingDirectory(
            self.dnd_widget,
            "Select Folder",
            self.last_directory
        )
        if folder:
            # Update last directory to the selected folder
            self.last_directory = folder
            # Get all files in the folder
            files = []
            for root, dirs, filenames in os.walk(folder):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
            self.load_files(files)
    
    def load_files(self, files):
        """Load files and update display"""
        self.loaded_files = files
        self.update_file_display()
        self.switch_to_work_area()
        self.files_loaded.emit(files)
    
    def clear_files(self):
        """Clear all loaded files and switch back to DnD area"""
        self.loaded_files = []
        self.switch_to_dnd_area()
        self.files_loaded.emit([])
    
    def process_files(self):
        """Process the loaded files - placeholder for future implementation"""
        print(f"Processing {len(self.loaded_files)} files...")
        # Add your file processing logic here
    
    def switch_to_work_area(self):
        """Switch to work area view"""
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(1)  # Work area is at index 1
            self.update_work_area_display()
    
    def switch_to_dnd_area(self):
        """Switch to DnD area view"""
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)  # DnD area is at index 0
    
    def update_file_display(self):
        """Update the file list display in work area"""
        if self.work_area_widget and self.loaded_files:
            self.update_work_area_display()
    
    def update_work_area_display(self):
        """Update the work area with loaded files"""
        if self.work_area_widget:
            file_label = self.work_area_widget.findChild(QLabel, "fileListLabel")
            if file_label:
                if self.loaded_files:
                    file_names = [os.path.basename(f) for f in self.loaded_files]
                    if len(file_names) > 10:
                        display_text = f"Loaded Files ({len(file_names)}):\n" + "\n".join(file_names[:10]) + f"\n... and {len(file_names) - 10} more files"
                    else:
                        display_text = f"Loaded Files ({len(file_names)}):\n" + "\n".join(file_names)
                    file_label.setText(display_text)
                else:
                    file_label.setText("No files loaded")
