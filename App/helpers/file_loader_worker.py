from PySide6.QtCore import QThread, Signal
from PIL import Image
import os

class FileLoaderWorker(QThread):
    """Worker thread for loading and validating image files"""
    progress_updated = Signal(int, str)  # progress_value, status_message
    file_processed = Signal(str, bool)   # file_path, is_valid
    loading_completed = Signal(list)     # valid_files
    loading_cancelled = Signal()
    
    def __init__(self, files):
        super().__init__()
        self.files = files
        self.cancelled = False
        self.valid_files = []
        
        # Supported image extensions by Pillow
        self.supported_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', 
            '.webp', '.ico', '.ppm', '.pgm', '.pbm', '.xbm', '.pcx',
            '.tga', '.sgi', '.eps', '.im', '.msp', '.dds', '.j2k', 
            '.jp2', '.jpx', '.jpc'
        }
        
    def run(self):
        """Main worker thread execution"""
        try:
            self.process_files()
        except Exception as e:
            print(f"Error in file loading worker: {e}")
        finally:
            if not self.cancelled:
                self.loading_completed.emit(self.valid_files)
            else:
                self.loading_cancelled.emit()
    
    def process_files(self):
        """Process and validate files"""
        total_files = len(self.files)
        processed_count = 0
        
        # Initial progress
        self.progress_updated.emit(0, f"Scanning {total_files} files...")
        for file_path in self.files:
            if self.cancelled:
                break
                
            # Check if file exists
            if not os.path.exists(file_path):
                processed_count += 1
                progress = int((processed_count / total_files) * 100)
                self.progress_updated.emit(progress, f"Skipped: {os.path.basename(file_path)} (not found)")
                self.file_processed.emit(file_path, False)
                continue
            
            # Check cancellation again before processing
            if self.cancelled:
                break
            
            # Check file extension first
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.supported_extensions:
                processed_count += 1
                progress = int((processed_count / total_files) * 100)
                self.progress_updated.emit(progress, f"Skipped: {os.path.basename(file_path)} (not an image)")
                self.file_processed.emit(file_path, False)
                continue
            
            # Check cancellation again before validation
            if self.cancelled:
                break
            
            # Try to validate the image file
            is_valid = self.validate_image_file(file_path)
            
            # Check cancellation after validation
            if self.cancelled:
                break
            
            if is_valid:
                self.valid_files.append(file_path)
                
            processed_count += 1
            progress = int((processed_count / total_files) * 100)
            
            status = f"Processing: {os.path.basename(file_path)}"
            if is_valid:
                status += " ✓"
            else:
                status += " ✗"
                
            self.progress_updated.emit(progress, status)
            self.file_processed.emit(file_path, is_valid)
            
            # Small delay to allow UI updates and cancellation - check cancellation after delay
            self.msleep(5)  # Reduced from 10ms to 5ms for better responsiveness
            if self.cancelled:
                break
    
    def validate_image_file(self, file_path):
        """Validate if file is a valid image that Pillow can open"""
        try:
            with Image.open(file_path) as img:
                # Try to load the image to verify it's valid
                img.verify()
                return True
        except Exception:
            return False
    
    def cancel(self):
        """Cancel the file loading operation"""
        self.cancelled = True
