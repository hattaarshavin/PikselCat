from PySide6.QtWidgets import QWidget, QLabel, QFileDialog, QPushButton, QStackedWidget
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent, QDragLeaveEvent
import qtawesome as qta
import os

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
        
        # Initialize PixelcutApiHelper for validation (create when needed)
        self.pixelcut_api = None
        
        # Rate limiting for API validation
        self.last_api_check_time = 0
        self.api_check_cache = {}  # Cache validation results temporarily
        self.cache_duration = 30000  # 30 seconds cache
        
        # Get the stacked widget for switching between DnD and Work Area
        self.stacked_widget = workspace_widget.findChild(QStackedWidget, "stackedWidget")
        self.setup_connections(open_files_btn, open_folder_btn)
        self.setup_drag_drop()
        self.setup_ui()
        
        # Initially show DnD area (index 0)
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)
        self.status_helper.show_ready("Drag & drop image files or select files/folder")
        
        # Set last_directory to user's home directory if not set
        self.last_directory = os.path.expanduser("~")
        
        # Disable run button initially since we're in DnD mode
        self._update_run_button_state(False)
    
    def _update_run_button_state(self, enabled):
        """Update run button enabled/disabled state"""
        try:
            # Get actions controller to update run button
            from App.controller.main_controller import MainController
            import gc
            for obj in gc.get_objects():
                if isinstance(obj, MainController) and hasattr(obj, 'actions_controller'):
                    actions_widget = obj.actions_controller.actions_widget
                    if actions_widget:
                        run_button = actions_widget.findChild(QWidget, "runButton")
                        if run_button:
                            run_button.setEnabled(enabled)
                    break
        except Exception as e:
            print(f"Error updating run button state: {e}")

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
        """Setup drag and drop functionality"""
        if self.dnd_widget:
            # Find all relevant widgets in hierarchy
            from PySide6.QtWidgets import QFrame
            
            # Enable drag & drop on workspace_widget (top level)
            self.workspace_widget.setAcceptDrops(True)
            
            # Enable on stacked widget
            if self.stacked_widget:
                self.stacked_widget.setAcceptDrops(True)
            
            # Find dnd container
            dnd_container = self.workspace_widget.findChild(QWidget, "dndContainer")
            if dnd_container:
                dnd_container.setAcceptDrops(True)
            
            # Enable on dnd_widget itself
            self.dnd_widget.setAcceptDrops(True)
            
            # Find dnd_frame
            dnd_frame = self.dnd_widget.findChild(QFrame, "dndFrame")
            if dnd_frame:
                self.dnd_frame = dnd_frame
                dnd_frame.setAcceptDrops(True)
            
            # Make child widgets properly handle drag events
            self._make_children_transparent(self.dnd_widget)
            
            # Override events on relevant widgets
            main_window = self.workspace_widget
            while main_window.parent():
                main_window = main_window.parent()
            
            self._override_drag_events(main_window)
            self._override_drag_events(self.workspace_widget)
            self._override_drag_events(self.stacked_widget)
            if dnd_container:
                self._override_drag_events(dnd_container)
            self._override_drag_events(self.dnd_widget)
            if dnd_frame:
                self._override_drag_events(dnd_frame)

    def _make_children_transparent(self, parent_widget):
        """Make child widgets properly handle drag events"""
        for child in parent_widget.findChildren(QWidget):
            if child != parent_widget and child != self.dnd_frame:
                if isinstance(child, QLabel):
                    child.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                    child.setAcceptDrops(True)
                elif isinstance(child, QPushButton):
                    child.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                    child.setAcceptDrops(True)
                else:
                    child.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                    child.setAcceptDrops(False)

    def _override_drag_events(self, widget):
        """Override drag events on a specific widget"""
        if widget:
            # Store original methods first
            if not hasattr(widget, '_original_drag_enter'):
                widget._original_drag_enter = widget.dragEnterEvent
                widget._original_drag_move = widget.dragMoveEvent
                widget._original_drag_leave = widget.dragLeaveEvent
                widget._original_drop = widget.dropEvent
            
            widget.dragEnterEvent = self.new_drag_enter
            widget.dragMoveEvent = self.new_drag_move
            widget.dragLeaveEvent = self.new_drag_leave
            widget.dropEvent = self.new_drop

    def new_drag_enter(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            self.on_drag_enter()
        else:
            event.ignore()

    def new_drag_move(self, event):
        """Handle drag move event"""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def new_drag_leave(self, event):
        """Handle drag leave event"""
        self.on_drag_leave()

    def new_drop(self, event):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            files = []
            urls = event.mimeData().urls()
            
            for url in urls:
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    files.append(file_path)
                elif os.path.isdir(file_path):
                    for root, dirs, filenames in os.walk(file_path):
                        for filename in filenames:
                            files.append(os.path.join(root, filename))
            
            if files:
                self.load_files(files)
                event.accept()
            else:
                event.ignore()
        else:
            event.ignore()
        
        self.on_drag_leave()
    
    def on_drag_enter(self):
        """Handle drag enter visual feedback"""
        self.status_helper.show_status("Files detected - Drop to load files", self.status_helper.PRIORITY_NORMAL)
        
        # Apply to the dnd frame for visual feedback
        if hasattr(self, 'dnd_frame') and self.dnd_frame:
            self.dnd_frame.setProperty("dragHover", True)
            self.dnd_frame.style().unpolish(self.dnd_frame)
            self.dnd_frame.style().polish(self.dnd_frame)
    
    def on_drag_leave(self):
        """Handle drag leave visual feedback"""
        # Remove from the dnd frame
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
            self.last_directory if self.last_directory else os.path.expanduser("~"),
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
            self.last_directory if self.last_directory else os.path.expanduser("~")
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
        # Don't check API key here - do it in background to avoid blocking
        # Just start loading immediately for better responsiveness
        
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
        
        # Show progress dialog and start worker immediately
        self.progress_dialog.show()
        self.file_loader_worker.start()
        
        self.status_helper.show_status("Loading image files...", self.status_helper.PRIORITY_NORMAL)
        
        # Check API key in background while files are loading
        self._check_api_key_background()
    
    def _check_api_key_background(self):
        """Check API key in background without blocking file loading"""
        if not hasattr(self, 'work_handler') or not self.work_handler:
            return
        
        config_manager = getattr(self.work_handler, 'config_manager', None)
        if not config_manager:
            return
        
        # Quick check without API call
        api_key = config_manager.get("api_headers", {}).get("X-API-KEY", "").strip()
        
        if not api_key:
            # Schedule settings dialog to show after file loading completes
            self._show_settings_after_loading = True
    
    def check_api_key(self):
        """Legacy method - now just returns True for compatibility"""
        return True
    
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
        
        # Check if we need to show settings dialog
        if hasattr(self, '_show_settings_after_loading') and self._show_settings_after_loading:
            self._show_settings_after_loading = False
            if valid_files:  # Only show if we have files to process
                self._prompt_api_key_for_files(valid_files)
                return
        
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
    
    def _prompt_api_key_for_files(self, valid_files):
        """Show API key prompt after files are loaded"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.status_helper.show_status("API key required - Opening settings...", self.status_helper.PRIORITY_HIGH)
        
        from App.controller.settings import SettingsController
        SettingsController.show_settings_dialog(
            self.work_handler.config_manager, 
            self.status_helper, 
            self.dnd_widget
        )
        
        # Check again after settings dialog
        api_key = self.work_handler.config_manager.get("api_headers", {}).get("X-API-KEY", "").strip()
        if api_key:
            # Now process the files
            if self.work_handler:
                self.work_handler.load_files(valid_files)
            self.files_loaded.emit(valid_files)
            self.status_helper.show_status(f"Processing {len(valid_files)} files...", self.status_helper.PRIORITY_NORMAL)
        else:
            self.status_helper.show_status("API key required to process files", self.status_helper.PRIORITY_HIGH)
    
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
