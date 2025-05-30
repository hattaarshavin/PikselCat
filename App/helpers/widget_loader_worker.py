from PySide6.QtCore import QTimer, QObject, Signal
import os

class WidgetCreationManager(QObject):
    """Manager for creating LoadedItemWidget instances with progress tracking in main thread"""
    progress_updated = Signal(int, str)  # progress_value, status_message
    widget_created = Signal(object)      # LoadedItemWidget instance
    loading_completed = Signal(list)     # list of created widgets
    loading_cancelled = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_paths = []
        self.parent_widget = None
        self.current_index = 0
        self.cancelled = False
        self.created_widgets = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.create_next_widget)
        self.timer.setSingleShot(True)
        
    def start_creation(self, file_paths, parent_widget):
        """Start widget creation process"""
        self.file_paths = file_paths
        self.parent_widget = parent_widget
        self.current_index = 0
        self.cancelled = False
        self.created_widgets = []
        
        if not file_paths:
            self.loading_completed.emit([])
            return
              # Start the creation process
        self.create_next_widget()
        
    def create_next_widget(self):
        """Create the next widget in the queue"""
        if self.cancelled:
            self.loading_cancelled.emit()
            return
            
        if self.current_index >= len(self.file_paths):
            # All widgets created
            self.loading_completed.emit(self.created_widgets)
            return
            
        file_path = self.file_paths[self.current_index]
        
        # Update progress
        progress = int(((self.current_index + 1) / len(self.file_paths)) * 100)
        filename = os.path.basename(file_path)
        status = f"Creating widget for: {filename}"
        self.progress_updated.emit(progress, status)
        
        # Check cancellation before creating widget
        if self.cancelled:
            self.loading_cancelled.emit()
            return
        
        try:
            # Create widget (this happens in main thread)
            from App.controller.loaded_item_widget import LoadedItemWidget
            widget = LoadedItemWidget(file_path, self.parent_widget)
            
            # Check cancellation after widget creation
            if self.cancelled:
                # Clean up the widget we just created
                widget.setParent(None)
                widget.deleteLater()
                self.loading_cancelled.emit()
                return
                
            self.created_widgets.append(widget)
            self.widget_created.emit(widget)
        except Exception as e:
            print(f"Error creating widget for {file_path}: {e}")
        
        self.current_index += 1
        
        # Schedule next widget creation with small delay for UI responsiveness
        if not self.cancelled:
            self.timer.start(5)  # Reduced from 10ms to 5ms for better responsiveness
    
    def cancel(self):
        """Cancel the widget loading operation"""
        self.cancelled = True
        self.timer.stop()
        # Emit cancelled signal immediately for instant feedback
        self.loading_cancelled.emit()
