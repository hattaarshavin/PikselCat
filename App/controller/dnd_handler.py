from PySide6.QtWidgets import QWidget, QLabel, QFileDialog, QPushButton
from PySide6.QtCore import QObject, Signal
import os

class DndHandler(QObject):
    # Signal emitted when files are loaded
    files_loaded = Signal(list)
    
    def __init__(self, dnd_widget: QWidget, workspace_widget: QWidget, open_files_btn: QPushButton, open_folder_btn: QPushButton):
        super().__init__()
        self.dnd_widget = dnd_widget
        self.workspace_widget = workspace_widget
        self.loaded_files = []
        self.last_directory = ""  # Track last used directory
        self.setup_connections(open_files_btn, open_folder_btn)
        
    def setup_connections(self, open_files_btn: QPushButton, open_folder_btn: QPushButton):
        """Setup button connections"""
        open_files_btn.clicked.connect(self.open_files)
        open_folder_btn.clicked.connect(self.open_folder)

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
        self.files_loaded.emit(files)
    
    def update_file_display(self):
        """Update the file list display in workspace"""
        if self.workspace_widget:
            file_label = self.workspace_widget.findChild(QLabel, "fileListLabel")
            if file_label:
                if self.loaded_files:
                    file_names = [os.path.basename(f) for f in self.loaded_files]
                    if len(file_names) > 5:
                        display_text = f"{len(file_names)} files loaded:\n" + "\n".join(file_names[:5]) + "\n..."
                    else:
                        display_text = f"{len(file_names)} files loaded:\n" + "\n".join(file_names)
                    file_label.setText(display_text)
                else:
                    file_label.setText("No files loaded")
