from PySide6.QtWidgets import QDialog, QLineEdit, QLabel, QPushButton
from PySide6.QtCore import QObject, Signal, QTimer, Qt
import qtawesome as qta
from App.helpers.pixelcut_api import PixelcutApiHelper

class SettingsController(QObject):
    """Controller for settings dialog with API key management"""
    # Signals
    api_key_validated = Signal(bool, str)  # success, message
    dialog_closed = Signal()
    
    def __init__(self, settings_dialog: QDialog, config_manager, status_helper):
        super().__init__()
        self.settings_dialog = settings_dialog
        self.config_manager = config_manager
        self.status_helper = status_helper
        
        # Initialize Pixelcut API helper for validation
        self.pixelcut_api = PixelcutApiHelper(self.config_manager)
        self.pixelcut_api.validation_completed.connect(self.on_validation_completed)
        
        # Get UI elements
        self.api_key_input = settings_dialog.findChild(QLineEdit, "apiKeyLineEdit")
        self.validation_icon = settings_dialog.findChild(QLabel, "validationIcon")
        self.status_label = settings_dialog.findChild(QLabel, "statusLabel")
        self.close_button = settings_dialog.findChild(QPushButton, "closeButton")
        
        # Validation timer for auto-validation with delay
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.validate_api_key)
        
        # Rate limiting and validation state - ADD MISSING ATTRIBUTES
        self.current_api_key = ""
        self.is_validating = False
        self.last_validation_time = 0
        self.min_validation_interval = 2000  # Minimum 2 seconds between validations
        self.validation_delay = 1000  # 1 second delay after typing stops
        
        self.setup_ui()
        self.setup_connections()
        self.load_current_api_key()
    
    def setup_ui(self):
        """Setup UI elements with icons and styling"""
        # Set window properties
        self.settings_dialog.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        self.settings_dialog.setModal(True)
        
        # Setup close button icon
        if self.close_button:
            close_icon = qta.icon('fa6s.xmark', color='white')
            self.close_button.setIcon(close_icon)
            # Remove inline styling - now handled by CSS
        
        # Setup initial validation icon (hidden)
        if self.validation_icon:
            self.validation_icon.hide()
    
    def setup_connections(self):
        """Setup signal connections"""
        if self.api_key_input:
            self.api_key_input.textChanged.connect(self.on_api_key_changed)
        
        if self.close_button:
            self.close_button.clicked.connect(self.close_dialog)
        
        # Connect dialog close event
        self.settings_dialog.finished.connect(self.on_dialog_finished)
    
    def load_current_api_key(self):
        """Load current API key from config"""
        current_key = self.config_manager.get("api_headers", {}).get("X-API-KEY", "")
        if self.api_key_input and current_key:
            self.api_key_input.setText(current_key)
    
    def on_api_key_changed(self, text):
        """Handle API key input changes with rate limiting"""
        # Stop any pending validation
        self.validation_timer.stop()
        
        # Check if we're already validating
        if self.is_validating:
            return
        
        # Reset validation state immediately when text changes
        self.set_validation_state("neutral")
        
        # Clear any potentially invalid API key and credits from config immediately
        current_saved_key = self.config_manager.get("api_headers", {}).get("X-API-KEY", "")
        if current_saved_key != text.strip():
            # API key changed from saved version, clear both API key and credits for safety
            self.config_manager.save_api_key("")
            self.config_manager.set("pixelcut_credits", {})
        
        if text.strip():
            # Check rate limiting
            import time
            current_time = int(time.time() * 1000)  # Current time in milliseconds
            
            time_since_last = current_time - self.last_validation_time
            
            if time_since_last < self.min_validation_interval:
                # Too soon, extend the delay
                remaining_time = self.min_validation_interval - time_since_last
                delay = max(self.validation_delay, remaining_time)
            else:
                delay = self.validation_delay
            
            # Start validation timer with calculated delay
            self.validation_timer.start(delay)
        else:
            self.set_validation_state("neutral")
            self.update_status("Enter API key to validate", "neutral")
    
    def validate_api_key(self):
        """Validate API key using PixelcutApiHelper"""
        if self.is_validating:
            return
        
        api_key = self.api_key_input.text().strip()
        if not api_key:
            return
        
        self.is_validating = True
        self.set_validation_state("validating")
        self.update_status("Validating API key...", "validating")
        
        # Use PixelcutApiHelper for validation
        self.pixelcut_api.validate_api_key(api_key)
    
    def on_validation_completed(self, success, message, credits):
        """Handle validation completion from PixelcutApiHelper"""
        try:
            if success and credits > 0:
                self.set_validation_state("valid")
                self.update_status(message, "valid")
                
                # SAVE API KEY hanya jika valid dan ada credits
                api_key = self.api_key_input.text().strip()
                if self.config_manager.save_api_key(api_key):
                    # Double-check that credits data is actually in the config
                    self.config_manager.reload_config()
                    credits_data = self.config_manager.get("pixelcut_credits", {})
                    
                    # If credits data is still empty, try to force save it again
                    if not credits_data or credits_data == {}:
                        # Get the data from validation cache
                        api_validation_cache = self.config_manager.get("api_validation_cache", {})
                        validation_cache = api_validation_cache.get("validation_cache", {})
                        if api_key in validation_cache:
                            cache_entry = validation_cache[api_key]
                            if cache_entry.get("valid") and cache_entry.get("credits", 0) > 0:
                                # Create a minimal credits structure
                                fallback_credits = {
                                    "creditsRemaining": cache_entry["credits"],
                                    "periods": [{
                                        "credits": 100,  # Assume 100 total for now
                                        "creditsRemaining": cache_entry["credits"],
                                        "creditsUsed": 100 - cache_entry["credits"],
                                        "periodStart": "2025-05-29T04:46:00.927526Z",
                                        "periodEnd": "2026-05-29T04:46:00.926Z",
                                        "gracePeriodEnd": "2026-06-08T04:46:00.926Z"
                                    }]
                                }
                                self.config_manager.config["pixelcut_credits"] = fallback_credits
                                self.config_manager.save_config()
                
                self.api_key_validated.emit(True, message)
                
                # Trigger immediate statistics refresh by updating last validation time
                import time
                self.last_validation_time = int(time.time() * 1000)
                
            else:
                self.set_validation_state("invalid")
                self.update_status(message, "invalid")
                
                # CLEAR invalid API key AND credits from config
                self.config_manager.save_api_key("")
                self.config_manager.set("pixelcut_credits", {})
                # Force save config to ensure changes are written
                self.config_manager.save_config()
                
                self.api_key_validated.emit(False, message)
                
        finally:
            self.is_validating = False
            print("API validation completed")
    
    def set_validation_state(self, state):
        """Set validation state and update UI accordingly"""
        if not self.api_key_input or not self.validation_icon:
            return
        
        # Update input field state
        self.api_key_input.setProperty("validationState", state)
        self.api_key_input.style().unpolish(self.api_key_input)
        self.api_key_input.style().polish(self.api_key_input)
        
        # Update validation icon
        if state == "valid":
            icon = qta.icon('fa6s.check', color='#28a745')
            self.validation_icon.setPixmap(icon.pixmap(20, 20))
            self.validation_icon.show()
        elif state == "invalid":
            icon = qta.icon('fa6s.xmark', color='#dc3545')
            self.validation_icon.setPixmap(icon.pixmap(20, 20))
            self.validation_icon.show()
        elif state == "validating":
            icon = qta.icon('fa6s.spinner', color='#ffc107')
            self.validation_icon.setPixmap(icon.pixmap(20, 20))
            self.validation_icon.show()
        else:  # neutral
            self.validation_icon.hide()
    
    def update_status(self, message, status_type):
        """Update status label with message and styling"""
        if not self.status_label:
            return
        
        self.status_label.setText(message)
        
        if status_type == "valid":
            self.status_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #28a745; margin-top: 5px;")
        elif status_type == "invalid":
            self.status_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #dc3545; margin-top: 5px;")
        elif status_type == "validating":
            self.status_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #ffc107; margin-top: 5px;")
        else:  # neutral
            self.status_label.setStyleSheet("font-size: 11px; font-style: italic; color: rgba(138, 142, 145, 0.8); margin-top: 5px;")
    
    def close_dialog(self):
        """Close the settings dialog"""
        self.settings_dialog.accept()
    
    def on_dialog_finished(self):
        """Handle dialog close event"""
        self.dialog_closed.emit()
    
    def show_dialog(self):
        """Show the settings dialog"""
        self.settings_dialog.exec()
    
    @staticmethod
    def show_settings_dialog(config_manager, status_helper, parent=None):
        """Static method to show settings dialog"""
        from App.helpers._ui_helper import UIHelper
        
        ui_helper = UIHelper()
        
        # Load settings UI using correct method
        try:
            settings_dialog = ui_helper.load_ui_file(
                config_manager.base_dir / "App" / "gui" / "dialogs" / "settings.ui"
            )
            
            if settings_dialog:
                # Set parent if provided
                if parent:
                    settings_dialog.setParent(parent)
                
                # Create controller
                controller = SettingsController(settings_dialog, config_manager, status_helper)
                controller.show_dialog()
                return controller
        except Exception as e:
            print(f"Error loading settings dialog: {e}")
            status_helper.show_error("Failed to load settings dialog")
        
        return None
