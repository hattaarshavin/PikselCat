from PySide6.QtWidgets import QWidget, QFileDialog
from PySide6.QtCore import QObject, Signal, QTimer
import qtawesome as qta
import os

class ActionsController(QObject):
    # Signals for when buttons are clicked
    run_clicked = Signal()
    stop_clicked = Signal()
    output_destination_changed = Signal(str)  # Emit when output path changes
    
    def __init__(self, actions_widget: QWidget, status_helper):
        super().__init__()
        self.actions_widget = actions_widget
        self.status_helper = status_helper
        self.output_path = ""  # Store selected output path
        # Store references for settings dialog
        self.config_manager = None
        
        self.setup_ui()
        self.connect_signals()
        # Set initial status
        self.status_helper.show_ready("System ready")
    
    def set_config_manager(self, config_manager):
        """Set config manager reference for settings dialog"""
        self.config_manager = config_manager
    
    def setup_ui(self):
        """Setup the UI elements with icons"""
        if self.actions_widget:
            # Find the settings button
            settings_button = self.actions_widget.findChild(QWidget, "settingsButton")
            if settings_button:
                # Add gear icon using QtAwesome fa6s
                gear_icon = qta.icon('fa6s.gear', color='white')
                settings_button.setIcon(gear_icon)
            
            # Find the run button
            run_button = self.actions_widget.findChild(QWidget, "runButton")
            if run_button:
                # Add play icon using QtAwesome fa6s
                play_icon = qta.icon('fa6s.play', color='white')
                run_button.setIcon(play_icon)
            
            # Find the stop button
            stop_button = self.actions_widget.findChild(QWidget, "stopButton")
            if stop_button:
                # Add stop icon using QtAwesome fa6s
                stop_icon = qta.icon('fa6s.stop', color='white')
                stop_button.setIcon(stop_icon)
            
            # Find the output destination button
            output_button = self.actions_widget.findChild(QWidget, "outputDestinationButton")
            if output_button:
                # Add folder icon using QtAwesome fa6s
                folder_icon = qta.icon('fa6s.folder-open', color='white')
                output_button.setIcon(folder_icon)
    
    def connect_signals(self):
        """Connect button signals to slots"""
        if self.actions_widget:
            # Connect settings button
            settings_button = self.actions_widget.findChild(QWidget, "settingsButton")
            if settings_button:
                settings_button.clicked.connect(self.on_settings_clicked)
            
            run_button = self.actions_widget.findChild(QWidget, "runButton")
            if run_button:
                run_button.clicked.connect(self.on_run_clicked)
            
            stop_button = self.actions_widget.findChild(QWidget, "stopButton")
            if stop_button:
                stop_button.clicked.connect(self.on_stop_clicked)
            
            # Connect output destination button
            output_button = self.actions_widget.findChild(QWidget, "outputDestinationButton")
            if output_button:
                output_button.clicked.connect(self.on_output_destination_clicked)
    
    def on_settings_clicked(self):
        """Handle settings button click"""
        try:
            # Try to get config manager if not set
            if not self.config_manager:
                config_manager = self.get_config_manager()
                if not config_manager:
                    self.status_helper.show_error("Configuration manager not available")
                    return
            else:
                config_manager = self.config_manager
            
            from App.controller.settings import SettingsController
            
            # Show settings dialog
            settings_controller = SettingsController.show_settings_dialog(
                config_manager, 
                self.status_helper, 
                self.actions_widget
            )
                
        except ImportError as e:
            print(f"Import error: {e}")
            self.status_helper.show_error("Settings module not found")
        except Exception as e:
            print(f"Error opening settings dialog: {e}")
            self.status_helper.show_error(f"Settings error: {str(e)}")
    
    def get_config_manager(self):
        """Try to get config manager from main controller"""
        try:
            from App.controller.main_controller import MainController
            import weakref
            for obj in weakref.get_objects():
                if isinstance(obj, MainController) and hasattr(obj, 'config_manager'):
                    return obj.config_manager
        except:
            pass
        return None
    
    def on_run_clicked(self):
        """Handle run button click with credit checking"""
        # Check if we have a work handler to validate credits
        work_handler = None
        try:
            # Try to get work handler reference from main controller
            from App.controller.main_controller import MainController
            import weakref
            for obj in weakref.get_objects():
                if isinstance(obj, MainController):
                    work_handler = obj.work_handler
                    break
        except:
            pass
        
        # Check credits before processing
        if work_handler and hasattr(work_handler, 'can_process_files'):
            if not work_handler.can_process_files():
                self.status_helper.show_status("Insufficient Pixelcut Generative Credits", self.status_helper.PRIORITY_HIGH)
                return
        
        # Check if output destination is set
        if not self.output_path:
            self.status_helper.show_status("Please select output destination first", self.status_helper.PRIORITY_HIGH)
            return
        
        self.status_helper.show_processing("execution")
        print("Run button clicked!")
        self.set_running_state(True)
        self.run_clicked.emit()
        self.status_helper.show_status("Process running - Click Stop to abort", self.status_helper.PRIORITY_HIGH)
    
    def on_stop_clicked(self):
        """Handle stop button click"""
        self.status_helper.show_status("Stopping process...", self.status_helper.PRIORITY_HIGH)
        print("Stop button clicked!")
        self.set_running_state(False)
        self.stop_clicked.emit()
        self.status_helper.show_ready("Process stopped")
    
    def on_output_destination_clicked(self):
        """Handle output destination button click - ultra fast"""
        # Use native dialog for better performance
        folder = QFileDialog.getExistingDirectory(
            self.actions_widget,
            "Select Output Folder",
            self.output_path if self.output_path else os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks  # Optimize dialog
        )
        
        if folder:
            # Set path immediately - no validation needed since user selected it
            self.output_path = folder
            self.update_output_path_label()
            
            # Show immediate feedback
            self.status_helper.show_status(f"Output folder set: {self.truncate_path(folder)}", self.status_helper.PRIORITY_NORMAL)
            
            # Emit signal immediately
            self.output_destination_changed.emit(folder)

    def update_output_path_label(self):
        """Update the output path label with truncated path - optimized"""
        path_label = self.actions_widget.findChild(QWidget, "outputPathLabel")
        if path_label:
            if self.output_path:
                # Quick truncation without file system access
                truncated_path = self.truncate_path(self.output_path)
                path_label.setText(truncated_path)
                path_label.setStyleSheet("color: #ff7f36; font-size: 11px; font-weight: bold; margin: 2px;")
            else:
                path_label.setText("No output folder selected")
                path_label.setStyleSheet("color: rgba(138, 142, 145, 0.8); font-size: 11px; font-style: italic; margin: 2px;")

    def truncate_path(self, path):
        """Truncate path to show last two folders only - ultra fast"""
        if not path:
            return ""
        
        try:
            # Fast path truncation without file system access or drive checking
            path = os.path.normpath(path)
            parts = path.split(os.sep)
            
            if len(parts) <= 2:
                # Short path, just show folder name
                return parts[-1] if parts else ""
            else:
                # Show only last two folders: parent/current
                parent_folder = parts[-2] if len(parts) > 1 else ""
                current_folder = parts[-1]
                return f"...{os.sep}{parent_folder}{os.sep}{current_folder}"
        except Exception:
            # Fallback to just the folder name
            return os.path.basename(path) if path else ""

    def get_output_path(self):
        """Get the current output path"""
        return self.output_path
    
    def get_output_destination(self):
        """Get the current output destination (alias for get_output_path)"""
        return self.output_path
    
    def set_output_path(self, path):
        """Set the output path programmatically - ultra fast"""
        # Set path immediately without any validation
        self.output_path = path
        self.update_output_path_label()
        self.output_destination_changed.emit(path)

    def set_running_state(self, is_running: bool):
        """Set the state of buttons based on running status"""
        if self.actions_widget:
            run_button = self.actions_widget.findChild(QWidget, "runButton")
            stop_button = self.actions_widget.findChild(QWidget, "stopButton")
            
            if run_button and stop_button:
                if is_running:
                    # When running: disable run button, enable stop button
                    run_button.setEnabled(False)
                    stop_button.setEnabled(True)
                else:
                    # When not running: enable run button, disable stop button
                    run_button.setEnabled(True)
                    stop_button.setEnabled(False)
    
    def get_selected_action(self):
        """Get the selected action - this should be retrieved from work handler"""
        # Note: The action selection is handled by work_handler's actionComboBox
        # This method is kept for API consistency but actual action should come from work_handler
        return None