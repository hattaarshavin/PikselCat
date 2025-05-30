from PySide6.QtWidgets import QWidget, QLabel, QSizePolicy, QHBoxLayout, QVBoxLayout, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import qtawesome as qta
from PIL import Image, ImageQt
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
        thumbnail = self.get_image_thumbnail()
          # Set the data
        if self.file_icon_label and thumbnail:
            self.file_icon_label.setPixmap(thumbnail)
            
        if self.file_name_label:
            # Truncate file name if too long
            truncated_name = self.truncate_filename(file_name, 40)
            self.file_name_label.setText(truncated_name)
            
        if self.file_path_label:
            # Truncate directory path
            display_path = self.truncate_path(file_dir, 50)
            self.file_path_label.setText(display_path)
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
    def get_image_thumbnail(self):
        """Generate thumbnail for image files"""
        try:
            # Check if file is an image by extension
            ext = os.path.splitext(self.file_path)[1].lower()
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.ico'}
            
            if ext not in image_extensions:
                # For non-image files, return a default file icon
                icon = qta.icon('fa6s.file', color='gray')
                return icon.pixmap(24, 24)
            
            # Try to open and create thumbnail for image files
            with Image.open(self.file_path) as img:
                # Convert to RGB if necessary (for transparency handling)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail maintaining aspect ratio
                img.thumbnail((24, 24), Image.Resampling.LANCZOS)
                
                # Convert PIL image to QPixmap
                qt_image = ImageQt.ImageQt(img)
                pixmap = QPixmap.fromImage(qt_image)
                
                return pixmap
                
        except Exception as e:
            # If thumbnail generation fails, return default file icon
            icon = qta.icon('fa6s.file', color='gray')
            return icon.pixmap(24, 24)
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
    
    def truncate_filename(self, filename, max_length):
        """Truncate filename if too long"""
        if len(filename) <= max_length:
            return filename
        
        # Split name and extension
        name, ext = os.path.splitext(filename)
        
        # Calculate available space for name (reserve space for extension and ellipsis)
        available_length = max_length - len(ext) - 3  # 3 for "..."
        
        if available_length > 0:
            return f"{name[:available_length]}...{ext}"
        else:
            # If extension is too long, just truncate the whole thing
            return f"{filename[:max_length-3]}..."
    
    def get_file_path(self):
        """Get the file path"""
        return self.file_path
