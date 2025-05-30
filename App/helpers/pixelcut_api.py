import requests
import json
from PySide6.QtCore import QObject, Signal, QThread

class PixelcutApiWorker(QThread):
    """Worker thread for Pixelcut API calls"""
    credits_received = Signal(dict)  # Emit credit data
    error_occurred = Signal(str)     # Emit error message
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
    
    def run(self):
        """Fetch credits from Pixelcut API"""
        try:
            # Get API config from config manager
            api_config = self.config_manager.get("api_endpoints", {})
            headers_config = self.config_manager.get("api_headers", {})
            
            credits_url = api_config.get("credits")
            if not credits_url:
                self.error_occurred.emit("Credits API URL not configured")
                return
            
            # Make API request
            response = requests.get(credits_url, headers=headers_config, timeout=10)
            
            if response.status_code == 200:
                credit_data = response.json()
                self.credits_received.emit(credit_data)
            else:
                self.error_occurred.emit(f"API request failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            self.error_occurred.emit(f"Invalid API response: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")

class PixelcutApiHelper(QObject):
    """Helper class for Pixelcut API operations"""
    credits_updated = Signal(int)    # Emit remaining credits
    credits_error = Signal(str)      # Emit error message
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.current_credits = 0
        self.api_worker = None
    
    def fetch_credits(self):
        """Fetch current credits from API"""
        if self.api_worker and self.api_worker.isRunning():
            return  # Already fetching
        
        self.api_worker = PixelcutApiWorker(self.config_manager)
        self.api_worker.credits_received.connect(self.on_credits_received)
        self.api_worker.error_occurred.connect(self.on_credits_error)
        self.api_worker.finished.connect(self.on_worker_finished)
        self.api_worker.start()
    
    def on_credits_received(self, credit_data):
        """Handle successful credit data reception"""
        # Extract credits from API response
        credits_remaining = credit_data.get("creditsRemaining", 0)
        if credits_remaining == 0:
            credits_remaining = credit_data.get("credits_remaining", 0)
        
        self.current_credits = credits_remaining
        self.credits_updated.emit(credits_remaining)
    
    def on_credits_error(self, error_message):
        """Handle credit fetch error"""
        # Fall back to cached value from config
        cached_credits = self.config_manager.get("pixelcut_credits", {}).get("creditsRemaining", 0)
        self.current_credits = cached_credits
        self.credits_error.emit(error_message)
    
    def on_worker_finished(self):
        """Clean up worker thread"""
        if self.api_worker:
            self.api_worker.deleteLater()
            self.api_worker = None
    
    def get_current_credits(self):
        """Get current credits count"""
        return self.current_credits
    
    def has_sufficient_credits(self, required_credits):
        """Check if current credits are sufficient for operation"""
        return self.current_credits >= required_credits
