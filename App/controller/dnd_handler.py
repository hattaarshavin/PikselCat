from PySide6.QtWidgets import QWidget, QLabel, QFileDialog, QPushButton, QStackedWidget
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent, QDragLeaveEvent
import qtawesome as qta
import os
import qtawesome as qta
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
    
    def __init__(self, dnd_widget: QWidget, workspace_widget: QWidget, open_files_btn: QPushButton, open_folder_btn: QPushButton, status_helper, work_handler=None):
        super().__init__()
        self.dnd_widget = dnd_widget
        self.workspace_widget = workspace_widget
        self.status_helper = status_helper
        self.work_handler = work_handler
        self.last_directory = ""  # Track last used directory
        
        # Progress dialog and worker thread
        self.progress_dialog = None
        self.file_loader_worker = None
        
        # Get the stacked widget for switching between DnD and Work Area
        self.stacked_widget = workspace_widget.findChild(QStackedWidget, "stackedWidget")
        self.setup_connections(open_files_btn, open_folder_btn)
        self.setup_drag_drop()
        self.setup_ui()
        
        # Initially show DnD area (index 0)
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)        # Set initial status
        self.status_helper.show_ready("Drag & drop image files or select files/folder")
    
    def setup_ui(self):
        """Setup the DnD area UI elements with icons"""
        # Setup DnD area icons only
        if self.dnd_widget:
            # Find and set icon for open files button
            open_files_btn = self.dnd_widget.findChild(QPushButton, "openFilesButton")
            if open_files_btn:
                file_icon = qta.icon('fa6s.file-image', color='white')
                open_files_btn.setIcon(file_icon)
            
            # Find and set icon for open folder button
            open_folder_btn = self.dnd_widget.findChild(QPushButton, "openFolderButton")
            if open_folder_btn:
                folder_icon = qta.icon('fa6s.folder-open', color='white')
                open_folder_btn.setIcon(folder_icon)
    def setup_connections(self, open_files_btn: QPushButton, open_folder_btn: QPushButton):
        """Setup button connections"""
        open_files_btn.clicked.connect(self.open_files)
        open_folder_btn.clicked.connect(self.open_folder)
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality using proper widget overlay"""
        if self.dnd_widget:
            # Find the dndFrame within the dnd_widget
            from PySide6.QtWidgets import QVBoxLayout, QFrame
            
            dnd_frame = self.dnd_widget.findChild(QFrame, "dndFrame")
            if dnd_frame:
                # Create overlay widget for drag and drop that covers only the frame
                self.drag_drop_overlay = DragDropWidget(dnd_frame)
                self.drag_drop_overlay.setGeometry(dnd_frame.rect())
                self.drag_drop_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                self.drag_drop_overlay.show()
                
                # Connect signals
                self.drag_drop_overlay.files_dropped.connect(self.load_files)
                self.drag_drop_overlay.drag_entered.connect(self.on_drag_enter)
                self.drag_drop_overlay.drag_left.connect(self.on_drag_leave)
                
                # Ensure overlay resizes with parent frame
                def resize_overlay():
                    if hasattr(self, 'drag_drop_overlay') and dnd_frame:
                        self.drag_drop_overlay.setGeometry(dnd_frame.rect())
                
                original_resize = dnd_frame.resizeEvent
                def new_resize_event(event):
                    if original_resize:
                        original_resize(event)
                    resize_overlay()
                dnd_frame.resizeEvent = new_resize_event
                self.dnd_frame = dnd_frame
            else:
                print("Warning: dndFrame not found in dnd_widget")
    
    def on_drag_enter(self):
        """Handle drag enter visual feedback"""
        self.status_helper.show_status("Files detected - Drop to load files", self.status_helper.PRIORITY_NORMAL)
        
        if hasattr(self, 'drag_drop_overlay'):
            self.drag_drop_overlay.setProperty("dragHover", True)
            self.drag_drop_overlay.style().unpolish(self.drag_drop_overlay)
            self.drag_drop_overlay.style().polish(self.drag_drop_overlay)
        # Also apply to the dnd frame for visual feedback
        if hasattr(self, 'dnd_frame') and self.dnd_frame:
            self.dnd_frame.setProperty("dragHover", True)
            self.dnd_frame.style().unpolish(self.dnd_frame)
            self.dnd_frame.style().polish(self.dnd_frame)
    
    def on_drag_leave(self):
        """Handle drag leave visual feedback"""
        # Remove status message on drag leave - let it return to previous state naturally
        
        if hasattr(self, 'drag_drop_overlay'):
            self.drag_drop_overlay.setProperty("dragHover", False)
            self.drag_drop_overlay.style().unpolish(self.drag_drop_overlay)
            self.drag_drop_overlay.style().polish(self.drag_drop_overlay)
        # Also remove from the dnd frame
        if hasattr(self, 'dnd_frame') and self.dnd_frame:
            self.dnd_frame.setProperty("dragHover", False)
            self.dnd_frame.style().unpolish(self.dnd_frame)
            self.dnd_frame.style().polish(self.dnd_frame)
    
    def open_files(self):
        """Open file dialog to select multiple image files"""
        # Create image file filter for common formats only
        image_filter = (
            "Image Files (*.jpg *.jpeg *.png *.tiff *.tif *.webp);;All Files (*.*)"
        )
        
        files, _ = QFileDialog.getOpenFileNames(
            self.dnd_widget,
            "Select Image Files",
            self.last_directory,
            image_filter
        )
        if files:
            # Update last directory to the directory of the first selected file
            self.last_directory = os.path.dirname(files[0])
            self.start_file_loading(files)
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
            
            # Get all files in the folder recursively
            files = []
            for root, dirs, filenames in os.walk(folder):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
            
            if files:
                self.start_file_loading(files)
            else:                
                self.status_helper.show_status("No files found in folder", self.status_helper.PRIORITY_NORMAL)
    
    def load_files(self, files):
        """Load files and delegate to work handler - now just calls start_file_loading"""
        self.start_file_loading(files)
    
    def start_file_loading(self, files):
        """Start threaded file loading with progress dialog"""
        from App.gui.dialogs.progress_dialog import ProgressDialog
        from App.helpers.file_loader_worker import FileLoaderWorker
        
        # Create and show progress dialog
        self.progress_dialog = ProgressDialog(self.dnd_widget)
        self.progress_dialog.cancel_requested.connect(self.cancel_file_loading)
        
        # Create and start worker thread
        self.file_loader_worker = FileLoaderWorker(files)
        self.file_loader_worker.progress_updated.connect(self.on_progress_updated)
        self.file_loader_worker.loading_completed.connect(self.on_loading_completed)
        self.file_loader_worker.loading_cancelled.connect(self.on_loading_cancelled)
        
        # Show progress dialog and start worker
        self.progress_dialog.show()
        self.file_loader_worker.start()
        
        self.status_helper.show_status("Loading image files...", self.status_helper.PRIORITY_NORMAL)
    
    def on_progress_updated(self, progress, status):
        """Handle progress updates from worker thread"""
        if self.progress_dialog:
            self.progress_dialog.set_value(progress)
            self.progress_dialog.set_status(status)
    def on_loading_completed(self, valid_files):
        """Handle completion of file validation - start widget creation"""
        if self.progress_dialog:
            # Don't close progress dialog yet - it will be used for widget creation
            self.progress_dialog.set_stage("widgets", 0)
        
        if valid_files:
            # Load valid files into work handler (this will start widget creation)
            if self.work_handler:
                # Pass the progress dialog to work handler for stage 2
                if hasattr(self, 'progress_dialog'):
                    self.work_handler.progress_dialog = self.progress_dialog
                self.work_handler.load_files(valid_files)
            self.files_loaded.emit(valid_files)
            
            self.status_helper.show_status(f"Creating widgets for {len(valid_files)} files...", self.status_helper.PRIORITY_NORMAL)
        else:
            # No valid files found - close progress dialog
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            self.status_helper.show_status("No valid image files found", self.status_helper.PRIORITY_NORMAL)
        
        # Clean up file validation worker
        if self.file_loader_worker:
            self.file_loader_worker.deleteLater()
            self.file_loader_worker = None
    
    def on_loading_cancelled(self):
        """Handle cancellation of file loading"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.status_helper.show_status("File loading cancelled", self.status_helper.PRIORITY_NORMAL)
        
        # Clean up worker
        if self.file_loader_worker:
            self.file_loader_worker.deleteLater()
            self.file_loader_worker = None
    def cancel_file_loading(self):
        """Cancel the file loading operation"""
        # Cancel file validation worker
        if self.file_loader_worker:
            self.file_loader_worker.cancel()
        
        # If work handler exists and has a widget manager, cancel that too
        if self.work_handler and hasattr(self.work_handler, 'widget_manager') and self.work_handler.widget_manager:
            self.work_handler.widget_manager.cancel()
    
    def set_work_handler(self, work_handler):
        """Set the work handler reference"""
        self.work_handler = work_handler
