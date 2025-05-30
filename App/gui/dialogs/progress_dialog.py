from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta

class ProgressDialog(QDialog):
    """Progress dialog for file loading operations"""
    cancel_requested = Signal()
    
    def __init__(self, parent=None):          
        super().__init__(parent)
        self.setup_ui()
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        
    def setup_ui(self):
        """Setup the progress dialog UI"""
        self.setWindowTitle("Loading Files")
        self.setMinimumSize(450, 160)
        self.setMaximumSize(600, 200)
        self.resize(480, 170)
        self.setObjectName("ProgressDialog")  # Set object name for CSS styling
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Title label
        self.title_label = QLabel("Processing image files...")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Status label
        self.status_label = QLabel("Scanning files...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelButton")  # Set object name for CSS styling
        self.cancel_button.setMinimumWidth(80)
        self.cancel_button.setMinimumHeight(30)
        
        # Add icon to cancel button
        cancel_icon = qta.icon('fa6s.xmark', color='white')
        self.cancel_button.setIcon(cancel_icon)
        
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
    def set_maximum(self, maximum):
        """Set the maximum value for the progress bar"""
        self.progress_bar.setMaximum(maximum)
        
    def set_value(self, value):
        """Set the current value of the progress bar"""
        self.progress_bar.setValue(value)
        
    def set_status(self, status):
        """Update the status label"""
        self.status_label.setText(status)
        
    def set_title(self, title):
        """Update the title label"""
        self.title_label.setText(title)
        
    def set_stage(self, stage_name, stage_progress=0):
        """Update the dialog for a specific loading stage"""
        if stage_name == "validation":
            self.set_title("Validating image files...")
        elif stage_name == "widgets":
            self.set_title("Creating file widgets...")
        else:            
            self.set_title(f"{stage_name}...")
            
        self.set_value(stage_progress)
    
    def on_cancel_clicked(self):
        """Handle cancel button click with immediate feedback"""
        # Immediately disable the button and show cancelling status
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Cancelling...")
        self.set_status("Cancelling operation...")
        
        # Emit cancel signal
        self.cancel_requested.emit()
    
    def enable_cancel(self):
        """Re-enable the cancel button"""
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
    
    def disable_cancel(self):
        """Disable the cancel button"""
        self.cancel_button.setEnabled(False)
