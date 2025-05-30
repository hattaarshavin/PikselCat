from PySide6.QtCore import QObject, Signal, QTimer

class StatusHelper(QObject):
    """Helper class for managing status bar updates with priorities and timeouts"""
    
    # Status priorities
    PRIORITY_LOW = 1
    PRIORITY_NORMAL = 2
    PRIORITY_HIGH = 3
    PRIORITY_ERROR = 4
    
    # Default timeouts based on priority
    TIMEOUT_CONFIG = {
        PRIORITY_LOW: 2000,      # 2 seconds for low priority
        PRIORITY_NORMAL: 4000,   # 4 seconds for normal
        PRIORITY_HIGH: 6000,     # 6 seconds for important
        PRIORITY_ERROR: 10000    # 10 seconds for errors
    }
    
    def __init__(self):
        super().__init__()
        self.status_bar = None
        self.current_priority = 0
        self.clear_timer = QTimer()
        self.clear_timer.setSingleShot(True)
        self.clear_timer.timeout.connect(self._clear_status)
    
    def set_status_bar(self, status_bar):
        """Set the status bar reference"""
        self.status_bar = status_bar
    
    def show_status(self, message: str, priority: int = PRIORITY_NORMAL, timeout: int = None):
        """
        Show status message with priority filtering
        
        Args:
            message: Status message to display
            priority: Message priority (use class constants)
            timeout: Custom timeout in milliseconds (optional)
        """
        if not self.status_bar:
            return
            
        # Only show if priority is equal or higher than current
        if priority >= self.current_priority:
            self.current_priority = priority
            
            # Use custom timeout or default based on priority
            if timeout is None:
                timeout = self.TIMEOUT_CONFIG.get(priority, self.TIMEOUT_CONFIG[self.PRIORITY_NORMAL])
            
            self.status_bar.showMessage(message)
            
            # Set timer to clear status and reset priority
            self.clear_timer.stop()
            self.clear_timer.start(timeout)
    
    def show_loading(self, operation: str):
        """Show loading status for significant operations"""
        self.show_status(f"Loading {operation}...", self.PRIORITY_NORMAL)
    
    def show_success(self, operation: str, count: int = None):
        """Show success status"""
        if count is not None:
            message = f"{operation} completed - {count} items processed"
        else:
            message = f"{operation} completed successfully"
        self.show_status(message, self.PRIORITY_NORMAL)
    
    def show_error(self, error_msg: str):
        """Show error status with high priority"""
        self.show_status(f"Error: {error_msg}", self.PRIORITY_ERROR)
    
    def show_ready(self, context: str = ""):
        """Show ready status"""
        message = f"Ready{' - ' + context if context else ''}"
        self.show_status(message, self.PRIORITY_LOW)
    
    def show_processing(self, operation: str, count: int = None):
        """Show processing status for significant operations"""
        if count is not None:
            message = f"Processing {count} files..."
        else:
            message = f"Processing {operation}..."
        self.show_status(message, self.PRIORITY_HIGH)
    
    def _clear_status(self):
        """Internal method to clear status and reset priority"""
        if self.status_bar:
            self.status_bar.clearMessage()
        self.current_priority = 0
    
    def clear(self):
        """Manually clear status"""
        self.clear_timer.stop()
        self._clear_status()
