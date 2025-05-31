import requests
import json
import os
import time
from PySide6.QtCore import QThread, Signal
from pathlib import Path


class PixelcutProcessorWorker(QThread):
    """Worker thread for Pixelcut remove background processing"""
    
    # Signals for communication with main thread
    progress_updated = Signal(int, str)  # progress percentage, status message
    file_processing_started = Signal(str)  # file being processed
    file_processed = Signal(str, str, bool)  # input_file, output_file, success
    processing_completed = Signal(int, int)  # total_processed, total_failed
    processing_cancelled = Signal()
    error_occurred = Signal(str)  # error message
    
    def __init__(self, config_manager, files, action, output_folder):
        super().__init__()
        self.config_manager = config_manager
        self.files = files
        self.action = action
        self.output_folder = output_folder
        self.is_cancelled = False
        self.processed_count = 0
        self.failed_count = 0
        
    def cancel(self):
        """Cancel the processing operation"""
        self.is_cancelled = True
        
    def run(self):
        """Process files using Pixelcut API"""
        try:
            if not self.files:
                self.error_occurred.emit("No files to process")
                return
                
            # Get API configuration
            api_config = self.config_manager.get("api_endpoints", {})
            headers_config = self.config_manager.get("api_headers", {})
            
            # Determine API endpoint based on action
            endpoint_url = None
            if self.action == "Remove Bg":
                endpoint_url = api_config.get("remove_background")
            elif self.action == "Upscale 2x":
                endpoint_url = api_config.get("upscale")
            elif self.action == "Upscale 4x":
                endpoint_url = api_config.get("upscale")
            
            if not endpoint_url:
                self.error_occurred.emit(f"API endpoint not configured for action: {self.action}")
                return
                
            api_key = headers_config.get("X-API-KEY", "").strip()
            if not api_key:
                self.error_occurred.emit("API key not configured")
                return
                
            # Ensure output folder exists
            os.makedirs(self.output_folder, exist_ok=True)
            
            total_files = len(self.files)
            self.progress_updated.emit(0, f"Starting {self.action} for {total_files} files...")
            
            for i, file_path in enumerate(self.files):
                if self.is_cancelled:
                    self.processing_cancelled.emit()
                    return
                try:
                    # Emit signal that this file is starting to be processed
                    self.file_processing_started.emit(file_path)
                    
                    # Update progress
                    progress = int((i / total_files) * 100)
                    filename = os.path.basename(file_path)
                    self.progress_updated.emit(progress, f"Processing {filename}...")
                    
                    # Process the file
                    success, output_file = self.process_single_file(file_path, endpoint_url, api_key)
                    
                    if success:
                        self.processed_count += 1
                        self.file_processed.emit(file_path, output_file, True)
                    else:
                        self.failed_count += 1
                        self.file_processed.emit(file_path, "", False)
                        
                    # Small delay to prevent overwhelming the API
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.failed_count += 1
                    self.file_processed.emit(file_path, "", False)
                    print(f"Error processing {file_path}: {e}")
                          # Final progress update
            self.progress_updated.emit(100, f"Completed: {self.processed_count} processed, {self.failed_count} failed")
            self.processing_completed.emit(self.processed_count, self.failed_count)
            
        except Exception as e:
            self.error_occurred.emit(f"Processing error: {str(e)}")
            
    def process_single_file(self, file_path, endpoint_url, api_key):
        """Process a single file with Pixelcut API"""
        try:
            # Prepare the request headers (don't include Content-Type for multipart data)
            headers = {
                'Accept': 'application/json',
                'X-API-KEY': api_key
            }
            
            # Prepare file for upload using the official API format
            with open(file_path, 'rb') as f:
                files = [
                    ('image', ('file', f, 'application/octet-stream'))
                ]
                  # Add action-specific parameters
                data = {}
                if self.action == "Remove Bg":
                    data['format'] = 'png'  # Request PNG format for transparency
                elif self.action == "Upscale 2x":
                    data['scale'] = '2'
                elif self.action == "Upscale 4x":
                    data['scale'] = '4'
                    
                # Make API request
                response = requests.post(
                    endpoint_url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60  # 60 second timeout for processing
                )
            
            if response.status_code == 200:
                # Parse the JSON response to get the result URL
                try:
                    result_data = response.json()
                    result_url = result_data.get('result_url')
                    
                    if not result_url:
                        print(f"No result URL in response for {file_path}")
                        return False, ""
                        
                    # Download the processed image
                    download_response = requests.get(result_url, timeout=30)
                    if download_response.status_code != 200:
                        print(f"Failed to download result for {file_path}")
                        return False, ""
                        
                    processed_image_data = download_response.content
                    
                except json.JSONDecodeError:
                    print(f"Invalid JSON response for {file_path}")
                    return False, ""
                
                # Generate output filename
                input_filename = Path(file_path)
                if self.action == "Remove Bg":
                    suffix = "_removed_bg"
                    extension = ".png"  # Remove background always outputs PNG
                elif self.action == "Upscale 2x":
                    suffix = "_upscaled_2x"
                    extension = input_filename.suffix
                elif self.action == "Upscale 4x":
                    suffix = "_upscaled_4x"
                    extension = input_filename.suffix
                else:
                    suffix = "_processed"
                    extension = input_filename.suffix
                    
                output_filename = f"{input_filename.stem}{suffix}{extension}"
                output_path = os.path.join(self.output_folder, output_filename)
                
                # Save the result
                with open(output_path, 'wb') as f:
                    f.write(processed_image_data)
                    
                return True, output_path
                
            else:
                # Handle API errors
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f'API error: {response.status_code}')
                except:
                    error_msg = f'API error: {response.status_code}'
                    
                print(f"API error for {file_path}: {error_msg}")
                return False, ""
                
        except requests.exceptions.Timeout:
            print(f"Timeout processing {file_path}")
            return False, ""
        except requests.exceptions.RequestException as e:
            print(f"Network error processing {file_path}: {e}")
            return False, ""
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, ""
