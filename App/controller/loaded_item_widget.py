from PySide6.QtWidgets import QWidget, QLabel, QSizePolicy, QHBoxLayout, QVBoxLayout, QFrame
from PySide6.QtCore import Qt
import qtawesome as qta
import os

class LoadedItemWidget(QWidget):
    """Widget representing a single loaded file item"""
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
          # Setup the UI programmatically
        self.setup_ui()
        self.populate_data()
    
    def setup_ui(self):
        """Create the widget UI programmatically"""
        # Set widget properties and object name for CSS targeting
        self.setObjectName("LoadedItemWidget")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        # Remove fixed height constraints to allow dynamic sizing
        
        # Create main widget layout (transparent container)
        main_widget_layout = QVBoxLayout(self)
        main_widget_layout.setContentsMargins(2, 2, 2, 2)
        main_widget_layout.setSpacing(0)
        
        # Create the styled frame that will contain all content
        self.item_frame = QFrame()
        self.item_frame.setObjectName("LoadedItemFrame")
        self.item_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.item_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # Create main horizontal layout inside the frame
        main_layout = QHBoxLayout(self.item_frame)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Create file icon label
        self.file_icon_label = QLabel()
        self.file_icon_label.setObjectName("file_icon_label")
        self.file_icon_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.file_icon_label.setMinimumSize(24, 24)
        self.file_icon_label.setMaximumSize(24, 24)
        self.file_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create text layout
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
          # File name label
        self.file_name_label = QLabel()
        self.file_name_label.setObjectName("file_name_label")
        self.file_name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.file_name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.file_name_label.setWordWrap(True)  # Allow text wrapping for long filenames
        
        # File size label
        self.file_size_label = QLabel()
        self.file_size_label.setObjectName("file_size_label")
        self.file_size_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.file_size_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # File path label
        self.file_path_label = QLabel()
        self.file_path_label.setObjectName("file_path_label")
        self.file_path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.file_path_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.file_path_label.setWordWrap(True)  # Allow text wrapping for long paths
          # Add labels to text layout
        text_layout.addWidget(self.file_name_label)
        text_layout.addWidget(self.file_size_label)
        text_layout.addWidget(self.file_path_label)
        
        # Add widgets to main layout
        main_layout.addWidget(self.file_icon_label)
        main_layout.addLayout(text_layout)
          # Add the frame to the main widget layout
        main_widget_layout.addWidget(self.item_frame)
    
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
            # With word wrap enabled, we can show longer paths
            display_path = self.truncate_path(file_dir, 80)  # Increased from 50 to 80
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
            '.mov': 'fa6s.file-video',        }
        
        icon_name = icon_map.get(ext, 'fa6s.file')
        return qta.icon(icon_name, color='gray')
    
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
