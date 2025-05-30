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
        
        # Supported image extensions - common formats only
        self.supported_extensions = {
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp'
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
        
        # Batch process files for better performance
        batch_size = 10
        for i in range(0, len(self.files), batch_size):
            if self.cancelled:
                break
                
            batch = self.files[i:i+batch_size]
            for file_path in batch:
                if self.cancelled:
                    break
                    
                # Quick existence check first
                if not os.path.exists(file_path):
                    processed_count += 1
                    continue
                
                # Quick extension check
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in self.supported_extensions:
                    processed_count += 1
                    continue
                
                # Fast validation
                is_valid = self.quick_validate_image_file(file_path)
                
                if is_valid:
                    self.valid_files.append(file_path)
                    
                processed_count += 1
                
                # Update progress every 5 files for better responsiveness
                if processed_count % 5 == 0 or processed_count == total_files:
                    progress = int((processed_count / total_files) * 100)
                    status = f"Processed {processed_count}/{total_files} files"
                    self.progress_updated.emit(progress, status)
                
                # Check cancellation more frequently
                if self.cancelled:
                    break
            
            # Minimal delay between batches
            if not self.cancelled and i + batch_size < len(self.files):
                self.msleep(1)  # Very small delay
    
    def quick_validate_image_file(self, file_path):
        """Fast image validation - just check if file can be opened"""
        try:
            # Get file size first - skip very small files
            file_size = os.path.getsize(file_path)
            if file_size < 100:  # Less than 100 bytes is likely not a valid image
                return False
            
            # Quick PIL check without full verification
            with Image.open(file_path) as img:
                # Just check format, don't verify entire file
                return img.format is not None
        except Exception:
            return False
    
    def cancel(self):
        """Cancel the file loading operation"""
        self.cancelled = True
