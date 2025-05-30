from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt
import qtawesome as qta
import os

class LoadedItemWidget(QWidget):
    """Widget representing a single loaded file item"""
    
    def __init__(self, file_path: str, ui_helper, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.ui_helper = ui_helper
        
        # Load the UI
        self.setup_ui()
        self.populate_data()
    def setup_ui(self):
        """Load the UI from the .ui file"""
        # Get the base directory (assuming this is called from main)
        from pathlib import Path
        from PySide6.QtWidgets import QSizePolicy
        base_dir = Path(__file__).parent.parent.parent
        
        # Load the UI
        widget = self.ui_helper.load_ui_file(
            self.ui_helper.get_widget_ui_path(base_dir, "loaded_item_widget.ui"),
            self
        )
        
        if widget:
            # Copy the loaded widget's layout to this widget
            layout = widget.layout()
            if layout:                
                self.setLayout(layout)
                  # Explicitly set size policy to ensure proper expansion
                self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                
                # Ensure the widget takes full horizontal space
                self.setMinimumWidth(0)  # Remove fixed minimum width
                self.setMaximumWidth(16777215)  # Ensure no maximum width constraint
                self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Enable styling
                
                # Force the layout to expand horizontally
                if layout:
                    layout.setSizeConstraint(layout.SizeConstraint.SetDefaultConstraint)
                
                # Get references to the UI elements
                self.file_icon_label = self.findChild(QLabel, "fileIconLabel")
                self.file_name_label = self.findChild(QLabel, "fileNameLabel")
                self.file_path_label = self.findChild(QLabel, "filePathLabel")
                self.file_size_label = self.findChild(QLabel, "fileSizeLabel")
    
    def populate_data(self):
        """Populate the widget with file data"""
        if not os.path.exists(self.file_path):
            return
            
        # Get file info
        file_name = os.path.basename(self.file_path)
        file_dir = os.path.dirname(self.file_path)
        file_size = self.get_file_size()
        file_icon = self.get_file_icon(file_name)
        
        # Set the data
        if self.file_icon_label:
            self.file_icon_label.setPixmap(file_icon.pixmap(24, 24))
            
        if self.file_name_label:
            self.file_name_label.setText(file_name)
            
        if self.file_path_label:
            # Truncate path if too long
            display_path = self.truncate_path(file_dir, 50)
            self.file_path_label.setText(display_path)
            
        if self.file_size_label:
            self.file_size_label.setText(file_size)
    
    def get_file_size(self):
        """Get formatted file size"""
        try:
            size_bytes = os.path.getsize(self.file_path)
            
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        except:
            return "Unknown"
    
    def get_file_icon(self, file_name):
        """Get appropriate icon for file type"""
        ext = os.path.splitext(file_name)[1].lower()
        
        # Define icon mappings
        icon_map = {
            # Images
            '.jpg': 'fa6s.image', '.jpeg': 'fa6s.image', '.png': 'fa6s.image', 
            '.gif': 'fa6s.image', '.bmp': 'fa6s.image', '.svg': 'fa6s.image',
            '.webp': 'fa6s.image', '.ico': 'fa6s.image',
            
            # Documents
            '.pdf': 'fa6s.file-pdf', '.doc': 'fa6s.file-word', '.docx': 'fa6s.file-word',
            '.xls': 'fa6s.file-excel', '.xlsx': 'fa6s.file-excel',
            '.ppt': 'fa6s.file-powerpoint', '.pptx': 'fa6s.file-powerpoint',
            '.txt': 'fa6s.file-lines', '.rtf': 'fa6s.file-lines',
            
            # Code files
            '.py': 'fa6s.file-code', '.js': 'fa6s.file-code', '.html': 'fa6s.file-code',
            '.css': 'fa6s.file-code', '.php': 'fa6s.file-code', '.cpp': 'fa6s.file-code',
            '.c': 'fa6s.file-code', '.java': 'fa6s.file-code', '.cs': 'fa6s.file-code',
            '.json': 'fa6s.file-code', '.xml': 'fa6s.file-code', '.yaml': 'fa6s.file-code',
            '.yml': 'fa6s.file-code',
            
            # Archives
            '.zip': 'fa6s.file-zipper', '.rar': 'fa6s.file-zipper', '.7z': 'fa6s.file-zipper',
            '.tar': 'fa6s.file-zipper', '.gz': 'fa6s.file-zipper',
            
            # Audio/Video
            '.mp3': 'fa6s.file-audio', '.wav': 'fa6s.file-audio', '.flac': 'fa6s.file-audio',
            '.mp4': 'fa6s.file-video', '.avi': 'fa6s.file-video', '.mkv': 'fa6s.file-video',
            '.mov': 'fa6s.file-video',
        }
        
        icon_name = icon_map.get(ext, 'fa6s.file')
        return qta.icon(icon_name, color='#666')
    
    def truncate_path(self, path, max_length):
        """Truncate path if too long"""
        if len(path) <= max_length:
            return path
        
        # Try to show the most relevant part of the path
        parts = path.split(os.sep)
        if len(parts) > 2:
            return f"...{os.sep}{os.sep.join(parts[-2:])}"
        else:
            return f"...{path[-max_length:]}"
    
    def get_file_path(self):
        """Get the file path"""
        return self.file_path
